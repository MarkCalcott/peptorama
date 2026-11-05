import { useRef } from "react";
import useStore from "../../store";

import Button from "./Button";
import styles from "./Card.module.css";

export default function Card({ id, title, children, minHeight = 0 }) {
  const visible = useStore((s) =>
    Object.values(s.panels).some((panel) => panel[id]),
  );
  const toggleCard = useStore((s) => s.toggleCard);
  const contentRef = useRef(null);
  const isDragging = useRef(false);

  const onPointerDown = (e) => {
    e.preventDefault();
    isDragging.current = true;
    const content = contentRef.current;
    const startY = e.clientY;
    const startHeight = content.offsetHeight;

    const onMove = (e) => {
      const newHeight = Math.max(minHeight, startHeight + e.clientY - startY);
      content.style.height = `${newHeight}px`;
    };

    const onUp = () => {
      isDragging.current = false;
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
    };

    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp);
  };

  return (
    <div
      id={id}
      className={`${styles.wrapper} ${visible ? "" : styles.hidden}`}
    >
      <div className={styles.card}>
        <div className={styles.head}>
          <h2>{title}</h2>
          <div className={styles.closeButtons}>
            <Button
              variant="close"
              onClick={() => {
                if (contentRef.current)
                  contentRef.current.style.height = `${minHeight}px`;
              }}
              aria-label={`Minimize ${title}`}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 18 18"
                stroke="currentColor"
                strokeWidth="4"
              >
                <line x1="1" y1="9" x2="17" y2="9" />
              </svg>
            </Button>
            <Button
              label="⤢"
              variant="close"
              onClick={() => {
                if (contentRef.current) contentRef.current.style.height = null;
              }}
              aria-label={`Expand ${title}`}
            />
            <Button
              variant="close"
              onClick={() => {
                toggleCard(id);
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
              aria-label={`Hide ${title}`}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 18 18"
                stroke="currentColor"
                strokeWidth="4"
              >
                <line x1="1" y1="1" x2="17" y2="17" />
                <line x1="17" y1="1" x2="1" y2="17" />
              </svg>
            </Button>
          </div>
        </div>
        <div className={styles.content} ref={contentRef}>
          {children}
        </div>
        <div className={styles.resizeHandle} onPointerDown={onPointerDown} />
      </div>
    </div>
  );
}
