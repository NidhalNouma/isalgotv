export default function EmptyTradeState({ newTaskFn }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center md:px-4 px-1 h-full">
      <h1 className="text-4xl sm:text-6xl font-semibold mb-2 text-title text-center">
        Let Tero Trade <br /> for you
      </h1>
      <h1 className="text-xl font-semibold mb-8 text-title/40 text-center">
        Connect your account and let Tero manage it for you
      </h1>
      <button className="btn-accent" onClick={newTaskFn}>
        Create task
      </button>
    </div>
  );
}
