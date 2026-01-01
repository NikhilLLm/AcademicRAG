export default function Button({ children }) {
  return (
    <button
      className="cursor-pointer bg-linear-to-b from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 shadow-[0px_4px_32px_0_rgba(99,102,241,.70)] px-6 py-3 rounded-xl border border-slate-500 text-white font-medium transition-colors"
    >
      {children}
    </button>
  );
}
