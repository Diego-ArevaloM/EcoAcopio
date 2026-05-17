import { useState, useEffect } from "react";

export function useClock() {
  const [time, setTime] = useState(new Date().toLocaleTimeString("es-PE"));
  
  useEffect(() => {
    const iv = setInterval(() => setTime(new Date().toLocaleTimeString("es-PE")), 1000);
    return () => clearInterval(iv);
  }, []);
  
  return time;
}