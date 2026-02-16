export default function TopBar() {
  const today = new Date().toLocaleDateString('en-NG', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <header className="bg-white border-b h-16 flex items-center justify-between px-6 fixed top-0 left-64 right-0 z-10">
      <div>
        <h1 className="text-lg font-semibold text-gray-800">
          Predictive Health Intelligence Platform
        </h1>
        <p className="text-xs text-gray-500">
          Early Warning & Outbreak Risk Forecasting – Nigeria
        </p>
      </div>
      <div className="flex items-center space-x-4">
        <div className="text-right">
          <div className="text-sm font-medium text-gray-700">{today}</div>
          <div className="text-xs text-green-600">● System Operational</div>
        </div>
      </div>
    </header>
  );
}
