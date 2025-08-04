import { Fragment, useState } from "react";
import EmptyTradeState from "./EmptyTradeState";
import NewTradeTask from "./NewTradeTask";

import { useUser } from "../contexts/UserContext";
import { UpgradePopup } from "./ui/Popup";

export default function TradeSection({}) {
  const { user } = useUser();
  const [newTask, setNewTask] = useState(false);
  const [upgrade, setUpgrade] = useState(false);
  return (
    <Fragment>
      {!newTask ? (
        <EmptyTradeState
          newTaskFn={
            user?.isLifetime ? () => setNewTask(true) : () => setUpgrade(true)
          }
        />
      ) : (
        <NewTradeTask close={() => setNewTask(false)} />
      )}

      {!user?.isLifetime && upgrade && (
        <UpgradePopup onClose={() => setUpgrade(false)} />
      )}
    </Fragment>
  );
}
