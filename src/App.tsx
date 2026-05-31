/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export default function App() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900 text-slate-200">
      <div className="max-w-2xl p-8 bg-slate-800 rounded-xl shadow-lg border border-slate-700 text-center">
        <h1 className="text-3xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
          Projet Python Généré avec Succès
        </h1>
        <p className="mb-6 text-slate-300">
          L'environnement actuel de prévisualisation (Google AI Studio) est <strong>strictement restreint à l'exécution de code Node.js/TypeScript</strong> et ne dispose pas des binaires système nécessaires (Python, OpenCV, FFmpeg, Tesseract).
        </p>
        <div className="text-left bg-slate-900 p-4 rounded-lg mb-6 border border-slate-700">
          <h2 className="text-xl text-white font-semibold mb-2">Comment exécuter votre projet :</h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-slate-400">
            <li>Le code Python complet (FastAPI, yt-dlp, OpenCV, Tesseract) a été généré proprement dans le dossier <code className="bg-slate-800 px-1 py-0.5 rounded text-cyan-300">/python_backend/</code> du workspace.</li>
            <li>Utilisez la fonctionnalité d'<strong>Export GitHub ou le téléchargement ZIP</strong> de l'environnement AI Studio.</li>
            <li>Sur votre machine locale, accédez au dossier <code className="bg-slate-800 px-1 py-0.5 rounded text-cyan-300">python_backend</code> :</li>
            <div className="mt-2 text-green-400 font-mono text-xs">
              <p>python3 -m venv venv</p>
              <p>source venv/bin/activate</p>
              <p>pip install -r requirements.txt</p>
              <p>uvicorn main:app --reload</p>
            </div>
          </ol>
        </div>
        <p className="text-sm text-slate-500 italic">Vérifiez les fichiers dans l'explorateur pour confirmer que toute l'architecture requise a été respectée.</p>
      </div>
    </div>
  );
}

