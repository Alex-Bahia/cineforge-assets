import { useState, useEffect } from "react"
import styles from "./Intro.module.css"

interface Props {
  onEnter: () => void
}

const TAGLINE = "FORJANDO O CINEMA DO FUTURO"

export default function Intro({ onEnter }: Props) {
  const [chars, setChars] = useState(0)

  useEffect(() => {
    if (chars >= TAGLINE.length) return
    const t = setTimeout(() => setChars((c) => c + 1), 55)
    return () => clearTimeout(t)
  }, [chars])

  return (
    <div className={styles.root}>
      <div className={styles.globe}>
        <div className={styles.arc1} />
        <div className={styles.arc2} />
        <div className={styles.arc3} />
        <div className={styles.dot} />
      </div>
      <h1 className={styles.tagline}>{TAGLINE.slice(0, chars)}</h1>
      {chars >= TAGLINE.length && (
        <button className={styles.btn} onClick={onEnter}>
          INICIAR LINK NEURAL
        </button>
      )}
    </div>
  )
}
