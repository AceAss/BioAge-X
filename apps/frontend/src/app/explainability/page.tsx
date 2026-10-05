"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Model, ShapBiomarker, BeeswarmPoint, WaterfallExplanation } from "@/lib/types";
import { ShapBeeswarmPlot } from "@/components/charts/ShapBeeswarmPlot";
import { WaterfallPlot } from "@/components/charts/WaterfallPlot";
import { Sparkles, HelpCircle, User, ArrowRight, Dna } from "lucide-react";

export default function ExplainabilityPage() {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>("");
  const [biomarkers, setBiomarkers] = useState<ShapBiomarker[]>([]);
  const [beeswarm, setBeeswarm] = useState<BeeswarmPoint[]>([]);
  const [waterfall, setWaterfall] = useState<WaterfallExplanation | null>(null);
  const [selectedSampleIdx, setSelectedSampleIdx] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function init() {
      try {
        const [mdList, dsList] = await Promise.all([api.listModels(), api.listDatasets()]);
        setModels(mdList);
        if (mdList.length > 0 && dsList.length > 0) {
          const mId = mdList[0].id;
          const dId = dsList[0].id;
          setSelectedModelId(mId);
          loadExplanation(mId, dId, 0);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  async function loadExplanation(modelId: string, datasetId: string, sampleIdx: number) {
    try {
      const res = await api.getExplainability(modelId, datasetId, 12, sampleIdx);
      setBiomarkers(res.global_biomarkers);
      setBeeswarm(res.beeswarm_sample);
      setWaterfall(res.waterfall_sample);
    } catch (err) {
      console.error(err);
    }
  }

  function handleSampleChange(idx: number) {
    setSelectedSampleIdx(idx);
    api.listDatasets().then((ds) => {
      if (ds.length > 0 && selectedModelId) {
        loadExplanation(selectedModelId, ds[0].id, idx);
      }
    });
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-black text-white">SHAP Model Explainability & Biomarker Attribution</h1>
          <p className="text-xs text-slate-400 mt-1">
            Global cohort importance rankings, beeswarm distributions, and sample-level waterfall decompositions.
          </p>
        </div>

        {/* Sample selector */}
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-semibold flex items-center gap-1.5">
            <User className="h-3.5 w-3.5 text-cyan-400" />
            Inspect Sample:
          </label>
          <select
            value={selectedSampleIdx}
            onChange={(e) => handleSampleChange(Number(e.target.value))}
            className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-white focus:outline-none font-mono"
          >
            {Array.from({ length: 15 }, (_, i) => (
              <option key={i} value={i}>
                BIOAGE_SYNTH_{i + 1 < 10 ? `00${i + 1}` : `0${i + 1}`}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Global Beeswarm Plot */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
        <ShapBeeswarmPlot biomarkers={biomarkers} beeswarmPoints={beeswarm} />
      </div>

      {/* Local Sample Waterfall Plot */}
      {waterfall && (
        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md">
          <WaterfallPlot waterfall={waterfall} />
        </div>
      )}

      {/* Biological Interpretation Helper Guide */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-6 backdrop-blur-md space-y-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <HelpCircle className="h-4 w-4 text-cyan-400" />
          How to Interpret SHAP Values in Biological Aging
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-400">
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4">
            <span className="font-bold text-slate-200 block mb-1">Global Feature Ranking</span>
            Features higher in the beeswarm chart exert the largest overall magnitude (|SHAP|) on biological age predictions across the entire patient cohort.
          </div>
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4">
            <span className="font-bold text-rose-400 block mb-1">Positive Attributions (+Δ)</span>
            Dots extending to the right of zero indicate that this feature level drives the predicted biological age higher (accelerated biological age).
          </div>
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4">
            <span className="font-bold text-emerald-400 block mb-1">Negative Attributions (-Δ)</span>
            Dots extending to the left indicate that this feature level buffers against molecular wear, lowering the estimated biological age.
          </div>
        </div>
      </div>
    </div>
  );
}
