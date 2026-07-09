import dynamic from "next/dynamic";
import { useMemo } from "react";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

type Props = {
  x: number[];
  probability: number[];
  realPart: number[];
  imaginaryPart: number[];
};

export function SimulationChart({ x, probability, realPart, imaginaryPart }: Props) {
  const traces = useMemo(
    () => [
      { x, y: probability, type: "scatter", mode: "lines", name: "|ψ|²" },
      { x, y: realPart, type: "scatter", mode: "lines", name: "Re(ψ)" },
      { x, y: imaginaryPart, type: "scatter", mode: "lines", name: "Im(ψ)" }
    ],
    [x, probability, realPart, imaginaryPart]
  );

  return (
    <Plot
      data={traces as never}
      layout={{
        title: "Wavefunction Components",
        paper_bgcolor: "#0b1020",
        plot_bgcolor: "#0b1020",
        font: { color: "#d9e2ff" },
        margin: { t: 40, l: 40, r: 20, b: 40 }
      }}
      style={{ width: "100%", height: "420px" }}
      useResizeHandler
    />
  );
}
