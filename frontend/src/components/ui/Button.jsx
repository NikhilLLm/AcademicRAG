export default function Button({ children, variant = "primary", ...props }) {
  const baseClass = "cursor-pointer px-6 py-3 rounded-xl border font-medium transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2";
  
  const variants = {
    primary: "bg-gradient-to-b from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 shadow-[0px_8px_32px_0_rgba(99,102,241,.60)] border-indigo-400 text-white hover:shadow-[0px_12px_40px_0_rgba(99,102,241,.80)]",
    secondary: "bg-gradient-to-b from-purple-600 to-indigo-700 hover:from-purple-700 hover:to-indigo-800 shadow-[0px_8px_32px_0_rgba(139,92,246,.60)] border-purple-400 text-white hover:shadow-[0px_12px_40px_0_rgba(139,92,246,.80)]"
  };

  return (
    <button
      className={`${baseClass} ${variants[variant] || variants.primary}`}
      {...props}
    >
      {children}
    </button>
  );
}
