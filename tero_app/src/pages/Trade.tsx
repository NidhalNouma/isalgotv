import { Fragment, useState } from "react";

import TradeEmptyState from "../components/TradeEmptyState";
import NewTradeTask from "../components/TradeNewTask";
import { UpgradePopup } from "../ui/Popup";

import { useUser } from "../contexts/UserContext";

function Trade() {
  const { user } = useUser();
  const [newTask, setNewTask] = useState<Boolean>(false);
  const [upgrade, setUpgrade] = useState<Boolean>(false);

  return (
    <Fragment>
      {newTask ? (
        <NewTradeTask close={() => setNewTask(false)} />
      ) : (
        <TradeEmptyState
          newTaskFn={() => {
            if (!user?.isLifetime) setUpgrade(true);
            else setNewTask(true);
          }}
        />
      )}
      {upgrade && <UpgradePopup onClose={() => setUpgrade(false)} />}
    </Fragment>
  );
}

export default Trade;
