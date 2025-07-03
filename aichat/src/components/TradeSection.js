import { Fragment, useState } from "react";
import EmptyTradeState from "./EmptyTradeState";
import NewTradeTask from "./NewTradeTask";

export default function TradeSection({}) {
  const [newTask, setNewTask] = useState(false);
  return (
    <Fragment>
      {!newTask ? (
        <EmptyTradeState newTaskFn={() => setNewTask(true)} />
      ) : (
        <NewTradeTask close={() => setNewTask(false)} />
      )}
    </Fragment>
  );
}
