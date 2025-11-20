export default function App() {
  return (
    <div style={{
      padding: '40px',
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f0f0f0',
      minHeight: '100vh'
    }}>
      <h1 style={{ color: '#333', fontSize: '48px' }}>✅ React is Working!</h1>
      <p style={{ color: '#666', fontSize: '24px' }}>
        If you can see this text, React and Vite are running correctly.
      </p>
      <div style={{
        marginTop: '30px',
        padding: '20px',
        backgroundColor: '#4CAF50',
        color: 'white',
        borderRadius: '8px'
      }}>
        <h2>Success! The dev server is operational.</h2>
      </div>
    </div>
  )
}
