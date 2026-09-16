import Topbar from "../components/features/Topbar";
import Panelbar from "../components/features/Panelbar";

import PanelLayout from "./PanelLayout";

export default function Dashboard() {
  return (
    <div>
      <Topbar />
      <Panelbar />
      <PanelLayout />
    </div>
  );
}
