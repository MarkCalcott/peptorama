import { useState } from "react";
import NodeSearch from "./NodeSearch";
import NodeHighlight from "./NodeHighlight";

export default function NodeFunctions({ type }) {
  return (
    <>
      <h3>{type[0].toUpperCase() + type.slice(1)} peptides</h3>

      <NodeHighlight type={type} />

      <hr />

      <NodeSearch type={type} />
    </>
  );
}
