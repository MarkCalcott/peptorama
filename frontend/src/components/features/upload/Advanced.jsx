import { useState } from "react";
import useStore from "@/store";
import Button from "@/components/ui/Button";

import {
  EDGE_SCHEMA,
  PREDICTED_PROCESSING_SCHEMA,
} from "./settingsSchema";

const read = (settings, path) =>
  path.split(".").reduce((n, k) => n[k], settings);

function SelectField({ field, settings }) {
  // Multiple options can be selected
  const toggle = useStore((s) => s.selectSetting);
  const current = read(settings, field.path);
  return (
    <>
      {field.help && <p className="info">{field.help}</p>}
      <div className="toggleButtonArea" aria-label={field.path}>
        {field.options.map((o) => (
          <Button
            key={String(o.value)}
            variant="toggle"
            active={current.includes(o.value)}
            aria-pressed={current.includes(o.value)}
            tooltip={o.tip}
            onClick={() => toggle(field.path, o.value)}
          >
            {o.label}
          </Button>
        ))}
      </div>
    </>
  );
}

function ToggleField({ field, settings }) {
  // One option can be selected
  const toggle = useStore((s) => s.setSetting);
  const current = read(settings, field.path);
  return (
    <>
      {field.help && <p className="info">{field.help}</p>}
      <div className="toggleButtonArea" aria-label={field.path}>
        {field.options.map((o) => (
          <Button
            key={String(o.value)}
            variant="toggle"
            active={current === o.value}
            aria-pressed={current === o.value}
            tooltip={o.tip}
            onClick={() => toggle(field.path, o.value)}
          >
            {o.label}
          </Button>
        ))}
      </div>
    </>
  );
}

function SliderField({ field, settings }) {
  const setSetting = useStore((s) => s.setSetting);
  const value = read(settings, field.path);
  const percentFilled = ((value - field.min) / (field.max - field.min)) * 100;
  return (
    <>
      <div className="info">{field.label}</div>
      <div className="flexRow" style={{ alignItems: "center" }}>
        <input
          className="rangeSlider"
          type="range"
          min={field.min}
          max={field.max}
          step={field.step}
          value={value}
          onChange={(e) => setSetting(field.path, Number(e.target.value))}
          style={{
            background: `linear-gradient(to right, var(--border-active) 0%, var(--border-active) ${percentFilled}%, var(--bg-hover) ${percentFilled}%, var(--bg-hover) 100%)`,
          }}
        />
        <div>
          {value === field.max ? value.toPrecision(3) : value.toPrecision(2)}{" "}
          {field.unit && field.unit}
        </div>
      </div>
    </>
  );
}

function RangeField({ field, settings }) {
  const setSetting = useStore((s) => s.setSetting);
  const min = read(settings, field.minPath);
  const minLimit = field.minLimit;
  const max = read(settings, field.maxPath);
  const maxLimit = field.maxLimit;

  const [localMin, setLocalMin] = useState(min);
  const [localMax, setLocalMax] = useState(max);

  const commitMin = (value = localMin) => {
    const clamped = Math.min(Math.max(Number(value), minLimit), localMax);
    setLocalMin(clamped);
    setSetting(field.minPath, clamped);
  };

  const commitMax = (value = localMax) => {
    const clamped = Math.min(Math.max(Number(value), localMin), maxLimit);
    setLocalMax(clamped);
    setSetting(field.maxPath, clamped);
  };

  return (
    <>
      <div className="info">{field.help}</div>
      <div className="flexRow" style={{ alignItems: "center" }}>
        <span className="info">Min: </span>
        <div className="flexRowSmall">
          <Button
            type="button"
            onClick={() => commitMin(Number(localMin) - field.step)}
          >
            -
          </Button>
          <input
            type="number"
            min={minLimit}
            max={maxLimit}
            step={field.step}
            value={localMin}
            onChange={(e) => setLocalMin(e.target.value)}
            onBlur={() => commitMin()}
          />
          <Button
            className="btn"
            type="button"
            onClick={() => commitMin(Number(localMin) + field.step)}
          >
            +
          </Button>
        </div>
        <span className="info">Max: </span>
        <div className="flexRowSmall">
          <Button
            className="btn"
            type="button"
            onClick={() => commitMax(Number(localMax) - field.step)}
          >
            -
          </Button>
          <input
            type="number"
            min={minLimit}
            max={maxLimit}
            step={field.step}
            value={localMax}
            onChange={(e) => setLocalMax(e.target.value)}
            onBlur={() => commitMax()}
          />
          <Button
            className="btn"
            type="button"
            onClick={() => commitMax(Number(localMax) + field.step)}
          >
            +
          </Button>
        </div>
        {field.unit && <span>{field.unit}</span>}
      </div>
    </>
  );
}

const KINDS = {
  select: SelectField,
  toggle: ToggleField,
  range: RangeField,
  slider: SliderField,
};

function SchemaSection({ schema, settings }) {
  return (
    <>
      {schema.map((section, i) => {
        if (!section.show || section.show(settings))
          return (
            <div key={i}>
              {section.legend && <h5>{section.legend}</h5>}
              {section.fields.map((field) => {
                const Field = KINDS[field.kind];
                return (
                  <Field
                    key={field.id || field.path}
                    field={field}
                    settings={settings}
                  />
                );
              })}
            </div>
          );
      })}
    </>
  );
}

export default function Known() {
  const settings = useStore((s) => s.data.settings);

  return (
    <>
      <h3>Advanced</h3>
      <div className="flexRow">
        <div className="box section">
          <h4>Edge creation</h4>
          <p>
            Broader options allow filtering on the created network, but create
            larger files. For larger datasets, it is recommended to determine
            parameters on a subset.
          </p>
          <SchemaSection schema={EDGE_SCHEMA} settings={settings} />
        </div>

        <div className="box section">
          <h4>Processing antiSMASH</h4>
          <p>
            How to extract predicted peptides from dropped antiSMASH files.
            Changing these settings will not alter already extracted peptides.
          </p>
          <SchemaSection
            schema={PREDICTED_PROCESSING_SCHEMA}
            settings={settings}
          />
        </div>
      </div>
    </>
  );
}
