import { useState, useEffect } from "react"
import Splash from "./phases/Splash"
import Intro from "./phases/Intro"
import Cockpit from "./phases/Cockpit"

type Phase = "splash" | "intro" | "cockpit"

export default function App() {
  const [phase, setPhase] = useState<Phase>("splash")

  useEffect(() => {
    const t = setTimeout(() => setPhase("intro"), 2400)
    return () => clearTimeout(t)
  }, [])

  return (
    <>
      {phase === "splash" && <Splash />}
      {phase === "intro" && <Intro onEnter={() => setPhase("cockpit")} />}
      {phase === "cockpit" && <Cockpit />}
    </>
  )
}
