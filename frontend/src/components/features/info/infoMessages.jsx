export const INFO_MESSAGES = {
  welcome: () => (
    <>
      <h3>Welcome to Peptorama</h3>
      <p>
        <span className="warning">First time here?</span> To get started, load
        example data using one of the example buttons in the top section of the
        upload panel and then click "Build network".
      </p>
    </>
  ),
  inputDiversity: () => (
    <>
      <h3>Diverse peptide example</h3>
      <p>
        A collection of known peptides and monomers have been added as input.
        These are selected to highlight automated generation and visualation of
        diverse structures.
      </p>
      <p>
        <span className="warning">Build network</span> (bottom-right of the
        upload panel) or open the{" "}
        <span className="warning">Monomers panel </span>(top-right in panel
        display bar) to explore.
      </p>
    </>
  ),
  inputAntibiotics: () => (
    <>
      <h3>Retrospective antibiotic discovery</h3>
      <p>
        A collection of calcium dependent antibiotics with recent discoveries
        treated as predicted peptides. Gramicidin S and tyrocidine A serve as a
        non-CDA antibiotic. Structures represent only the linear peptide chains.
      </p>
      <p>
        <span className="warning">Build network</span> (bottom-right of the
        upload panel) to explore.
      </p>
    </>
  ),
  inputSiderophores: () => (
    <>
      <h3>Biodiscovery of pyoverdine siderophores</h3>
      <p>
        A comparison between all known pyoverdine peptide chains and antiSMASH
        results from 30 environmentally isolated bacteria.
      </p>
      <p>
        <span className="warning">Build network</span> (bottom-right of the
        upload panel) to explore.
      </p>
    </>
  ),
  knownUpload: () => (
    <>
      <h3>Known peptide upload</h3>
      <p>
        Upload peptides from a CSV file or manually input one peptide per line.
      </p>
    </>
  ),
  predictedUpload: () => (
    <>
      <h3>Predicted peptide upload</h3>
      <p>
        Upload predicted peptides from antiSMASH outputs or as manual inputs.
        Drop antiSMASH folders or the JSON (quicker) files to extract peptides.
      </p>
    </>
  ),
  monomerUpload: () => (
    <>
      <h3>Monomers upload</h3>
      <p>
        Monomers can (optionally) be extracted from known and predicted peptides
        prior to submitting a job. This allows manual inspection to confirm
        monomers are extracted as expected.
      </p>
      <p>
        Previously extracted monomers can be downloaded as a CSV file for
        editing and subsequent upload.
      </p>
    </>
  ),
  monomersExtracted: () => (
    <>
      <h3>Monomers extracted</h3>
      <p>
        Monomers were successfully extracted. View a graph and table of
        extracted monomers in the monomers panel or graphs of any metadata in
        the metadata panel.
      </p>
    </>
  ),
  submitSuccess: () => (
    <>
      <h3>Network created</h3>
      <p>A network was created and is viewable within the network panel. </p>
      <p>
        <span className="warning">Open other panels to explore:</span>
      </p>
      <ul>
        <li>Nodes: Peptide related display</li>
        <li>Edges: Adjust the connections between peptides</li>
        <li>Alignment: Selected alignments</li>
        <li>Selection: Selected metadata and chemical structures</li>
        <li>
          Monomers: View all monomers within the network and edit for subsequent
          builds
        </li>
        <li>Metadata: Graphical display of metadata</li>
      </ul>
    </>
  ),
  // Dummy example: reads params.
  dummy: ({ count, unknown }) => (
    <p>
      Extracted <strong>{count}</strong> monomers
      {unknown > 0 && (
        <>
          {" "}
          — <span className="warning">{unknown} unrecognised</span>. Resolve
          them in the monomer table.
        </>
      )}
      .
    </p>
  ),
};
