"""
Payment Service - Unified payment processing with Stripe and PayPal support
Handles payment processing for both providers in parallel
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime
import stripe
import paypalrestsdk
from decimal import Decimal

from app.config import settings
from app.models import Payment, PaymentProvider, PaymentStatus, Subscription
from app.schemas import PaymentCreate


# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Initialize PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # sandbox or live
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})


class StripePaymentService:
    """Stripe payment processing"""

    @staticmethod
    async def create_customer(email: str, name: str, metadata: Dict = None) -> str:
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    async def create_payment_intent(
        amount: Decimal,
        currency: str,
        customer_id: str,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Create Stripe payment intent"""
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )

            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "status": intent.status
            }
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    async def create_subscription(
        customer_id: str,
        price_id: str,
        trial_days: int = 0
    ) -> Dict[str, Any]:
        """Create Stripe subscription"""
        try:
            subscription_params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
            }

            if trial_days > 0:
                subscription_params["trial_period_days"] = trial_days

            subscription = stripe.Subscription.create(**subscription_params)

            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end)
            }
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    async def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> bool:
        """Cancel Stripe subscription"""
        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                stripe.Subscription.delete(subscription_id)
            return True
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    async def create_invoice(
        customer_id: str,
        items: list,
        auto_advance: bool = True
    ) -> Dict[str, Any]:
        """Create Stripe invoice"""
        try:
            # Create invoice items
            for item in items:
                stripe.InvoiceItem.create(
                    customer=customer_id,
                    amount=int(item["amount"] * 100),
                    currency=item.get("currency", "usd"),
                    description=item.get("description", "")
                )

            # Create and finalize invoice
            invoice = stripe.Invoice.create(
                customer=customer_id,
                auto_advance=auto_advance
            )

            if auto_advance:
                invoice.finalize_invoice()

            return {
                "invoice_id": invoice.id,
                "invoice_pdf": invoice.invoice_pdf,
                "hosted_invoice_url": invoice.hosted_invoice_url,
                "status": invoice.status
            }
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    @staticmethod
    async def verify_webhook(payload: str, signature: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")


class PayPalPaymentService:
    """PayPal payment processing"""

    @staticmethod
    async def create_order(
        amount: Decimal,
        currency: str,
        description: str,
        return_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create PayPal order"""
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": description
                }]
            })

            if payment.create():
                # Get approval URL
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break

                return {
                    "payment_id": payment.id,
                    "approval_url": approval_url,
                    "status": payment.state
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PayPal error: {payment.error}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PayPal error: {str(e)}"
            )

    @staticmethod
    async def execute_payment(payment_id: str, payer_id: str) -> Dict[str, Any]:
        """Execute PayPal payment after user approval"""
        try:
            payment = paypalrestsdk.Payment.find(payment_id)

            if payment.execute({"payer_id": payer_id}):
                return {
                    "payment_id": payment.id,
                    "status": payment.state,
                    "payer_email": payment.payer.payer_info.email,
                    "amount": payment.transactions[0].amount.total
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PayPal error: {payment.error}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PayPal error: {str(e)}"
            )

    @staticmethod
    async def create_billing_agreement(
        name: str,
        description: str,
        return_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create PayPal billing agreement for subscriptions"""
        try:
            billing_agreement = paypalrestsdk.BillingAgreement({
                "name": name,
                "description": description,
                "start_date": (datetime.utcnow()).isoformat() + "Z",
                "payer": {
                    "payment_method": "paypal"
                },
                "plan": {
                    "id": "plan_id"  # You need to create billing plans first
                }
            })

            if billing_agreement.create():
                for link in billing_agreement.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break

                return {
                    "token": billing_agreement.token,
                    "approval_url": approval_url
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PayPal error: {billing_agreement.error}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PayPal error: {str(e)}"
            )

    @staticmethod
    async def verify_webhook(headers: Dict, body: str) -> bool:
        """Verify PayPal webhook signature"""
        # PayPal webhook verification
        # This requires additional setup with PayPal webhook validation
        try:
            # Implement PayPal webhook verification
            # https://developer.paypal.com/docs/api/webhooks/v1/#verify-webhook-signature
            return True  # Placeholder
        except Exception:
            return False


class PaymentService:
    """Unified payment service coordinating Stripe and PayPal"""

    @staticmethod
    async def create_payment(
        db: AsyncSession,
        user_id: int,
        payment_data: PaymentCreate
    ) -> Payment:
        """Create payment record and initiate processing"""
        # Create payment record
        payment = Payment(
            user_id=user_id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            provider=payment_data.payment_provider,
            description=payment_data.description,
            credits_purchased=payment_data.credits_to_purchase or 0,
            status=PaymentStatus.PENDING
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        # Process payment based on provider
        if payment_data.payment_provider == PaymentProvider.STRIPE:
            # Stripe payment intent
            result = await StripePaymentService.create_payment_intent(
                amount=payment_data.amount,
                currency=payment_data.currency,
                customer_id=payment_data.payment_method_id,  # Stripe customer ID
                metadata={"payment_id": payment.id}
            )

            payment.provider_payment_id = result["payment_intent_id"]
            payment.metadata = result

        elif payment_data.payment_provider == PaymentProvider.PAYPAL:
            # PayPal order
            result = await PayPalPaymentService.create_order(
                amount=payment_data.amount,
                currency=payment_data.currency,
                description=payment_data.description or "Payment",
                return_url="https://yourapp.com/payment/success",
                cancel_url="https://yourapp.com/payment/cancel"
            )

            payment.provider_payment_id = result["payment_id"]
            payment.metadata = result

        payment.status = PaymentStatus.PROCESSING
        await db.commit()
        await db.refresh(payment)

        return payment

    @staticmethod
    async def process_successful_payment(
        db: AsyncSession,
        payment_id: int,
        provider_payment_id: str
    ) -> Payment:
        """Process successful payment (called by webhooks)"""
        payment = await db.get(Payment, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        payment.status = PaymentStatus.SUCCEEDED
        payment.paid_at = datetime.utcnow()
        payment.provider_payment_id = provider_payment_id

        # Add credits to user if this was a credit purchase
        if payment.credits_purchased > 0:
            from app.services.subscription_service import SubscriptionService
            await SubscriptionService.add_credits_after_payment(db, payment_id)

        await db.commit()
        await db.refresh(payment)

        return payment

    @staticmethod
    async def process_failed_payment(
        db: AsyncSession,
        payment_id: int,
        error_message: str
    ) -> Payment:
        """Process failed payment"""
        payment = await db.get(Payment, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        payment.status = PaymentStatus.FAILED
        payment.failed_at = datetime.utcnow()
        payment.failure_message = error_message

        await db.commit()
        await db.refresh(payment)

        return payment

    @staticmethod
    async def refund_payment(
        db: AsyncSession,
        payment_id: int,
        reason: Optional[str] = None
    ) -> Payment:
        """Refund a payment"""
        payment = await db.get(Payment, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        if payment.status != PaymentStatus.SUCCEEDED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only refund successful payments"
            )

        # Process refund with provider
        if payment.provider == PaymentProvider.STRIPE:
            try:
                refund = stripe.Refund.create(
                    payment_intent=payment.provider_payment_id,
                    reason=reason or "requested_by_customer"
                )
                payment.metadata["refund_id"] = refund.id
            except stripe.error.StripeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Refund failed: {str(e)}"
                )

        elif payment.provider == PaymentProvider.PAYPAL:
            # PayPal refund logic
            try:
                sale = paypalrestsdk.Sale.find(payment.provider_payment_id)
                refund = sale.refund({})
                if refund.success():
                    payment.metadata["refund_id"] = refund.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Refund failed: {refund.error}"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Refund failed: {str(e)}"
                )

        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = datetime.utcnow()

        # Deduct credits if applicable
        if payment.credits_purchased > 0:
            from app.services.user_service import UserService
            user = await UserService.get_by_id(db, payment.user_id)
            if user:
                user.credits = max(0, user.credits - payment.credits_purchased)

        await db.commit()
        await db.refresh(payment)

        return payment

    @staticmethod
    async def create_credit_purchase_session(
        db: AsyncSession,
        user: Any,
        amount: int,
        credits: int,
        bonus_credits: int = 0
    ) -> str:
        """
        Create Stripe checkout session for credit purchase

        Args:
            db: Database session
            user: User model instance
            amount: Purchase amount in USD
            credits: Total credits to grant (base + bonus)
            bonus_credits: Bonus credits amount

        Returns:
            Stripe checkout session URL
        """
        try:
            # Create Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'{credits} Credits',
                            'description': f'Base: {credits - bonus_credits} + Bonus: {bonus_credits}',
                        },
                        'unit_amount': amount * 100,  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{settings.FRONTEND_URL}/dashboard/credits?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/dashboard/credits?canceled=true",
                customer_email=user.email,
                metadata={
                    'user_id': str(user.id),
                    'credits': str(credits),
                    'base_credits': str(credits - bonus_credits),
                    'bonus_credits': str(bonus_credits),
                    'type': 'credit_purchase'
                }
            )

            # Create pending payment record
            payment = Payment(
                user_id=user.id,
                amount=Decimal(str(amount)),
                currency='USD',
                status=PaymentStatus.PENDING,
                provider=PaymentProvider.STRIPE,
                provider_payment_id=session.id,
                description=f'Credit purchase: {credits} credits',
                credits_purchased=credits
            )

            db.add(payment)
            await db.commit()

            return session.url

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )
