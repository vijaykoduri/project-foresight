export default function LoadingSpinner({ size = 'md', text = '' }) {
  return (
    <div className={`loading-spinner loading-${size}`}>
      <div className="spinner" />
      {text && <p className="loading-text">{text}</p>}
    </div>
  );
}
