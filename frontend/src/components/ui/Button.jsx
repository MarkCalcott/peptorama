import styles from "./Button.module.css";

export default function Button({
  label,
  onClick,
  variant = "default",
  size = "small",
  ariaLabel = null,
  active = false,
  disabled = false,
  tooltip = null,
  tooltipPosition = "bottom",
  children,
}) {
  return (
    <button
      className={`${styles.btn} ${styles[variant] || ""} ${styles[size] || ""} ${active ? styles.active : ""} ${tooltip ? styles.hasTooltip : ""}`}
      onClick={onClick}
      aria-label={ariaLabel}
      disabled={disabled}
      data-tooltip={tooltip || undefined}
      data-tooltip-pos={tooltip ? tooltipPosition : undefined}
    >
      {children || label}
    </button>
  );
}
