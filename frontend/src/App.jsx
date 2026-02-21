import { useState } from "react";
import axios from "axios";

const API_URL = "http://localhost:8000/api/analyze/";

export default function App() {
  // Question Card Component
  function QuestionCard({ question, rank }) {
    const [showVariants, setShowVariants] = useState(false);

    const priorityColors = {
      High: { bg: "#ffebee", border: "#ef5350", badge: "#d32f2f", icon: "🔥" },
      Medium: { bg: "#fff8e1", border: "#ffb74d", badge: "#f57c00", icon: "⚡" },
      Low: { bg: "#f3f4f6", border: "#9e9e9e", badge: "#616161", icon: "💡" },
    };

    const colors = priorityColors[question.priority];

    return (
      <div style={{
        ...styles.questionCard,
        background: colors.bg,
        borderLeft: `4px solid ${colors.border}`,
      }}>
        <div style={styles.cardHeader}>
          <span style={styles.rank}>#{rank}</span>
          <div style={styles.cardContent}>
            <div style={styles.cardMeta}>
              <span style={{ ...styles.priorityBadge, background: colors.badge }}>
                {colors.icon} {question.priority.toUpperCase()} PRIORITY
              </span>
              <span style={styles.countBadge}>
                Appears {question.count}× across papers
              </span>
            </div>

            <p style={styles.questionText}>{question.representative}</p>

            {question.variants.length > 1 && (
              <>
                <button
                  onClick={() => setShowVariants(!showVariants)}
                  style={styles.variantToggle}
                >
                  {showVariants ? "▲ Hide" : "▼ Show"} {question.variants.length} variant{question.variants.length > 1 ? "s" : ""}
                </button>

                {showVariants && (
                  <div style={styles.variantList}>
                    {question.variants.map((variant, i) => (
                      <div key={i} style={styles.variantItem}>
                        <span style={styles.variantSource}>📄 {variant.source}</span>
                        <p style={styles.variantText}>{variant.text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    );
  }
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("All");


  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const pdfFiles = selectedFiles.filter(f => f.type === "application/pdf");

    if (pdfFiles.length === 0) {
      setError("Please select only PDF files");
      return;
    }

    setFiles(pdfFiles);
    setError(null);
  };

  // Remove a file from the list
  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  // Send files to Django
  const handleAnalyze = async () => {
    if (files.length === 0) {
      setError("Please upload at least one PDF file");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    files.forEach(file => {
      formData.append("papers", file);
    });

    try {
      const response = await axios.post(API_URL, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to analyze papers. Is Django running?");
    } finally {
      setLoading(false);
    }
  };

  // Reset to upload more files
  const handleReset = () => {
    setFiles([]);
    setResult(null);
    setError(null);
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>PYQ Analyzer</h1>
      <p style={styles.subtitle}>Upload previous year question papers to get ranked priorities</p>

      {!result ? (
        // Upload section
        <div style={styles.uploadSection}>
          <input
            type="file"
            multiple
            accept="application/pdf"
            onChange={handleFileChange}
            style={styles.fileInput}
          />

          {files.length > 0 && (
            <div style={styles.fileList}>
              <h3>Selected Files ({files.length})</h3>
              {files.map((file, index) => (
                <div key={index} style={styles.fileItem}>
                  <span>{file.name}</span>
                  <button onClick={() => removeFile(index)} style={styles.removeBtn}>
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          {error && <div style={styles.error}>{error}</div>}

          <button
            onClick={handleAnalyze}
            disabled={loading || files.length === 0}
            style={{
              ...styles.analyzeBtn,
              ...(loading || files.length === 0 ? styles.btnDisabled : {})
            }}
          >
            {loading ? "Analyzing..." : `Analyze ${files.length} Paper${files.length !== 1 ? 's' : ''}`}
          </button>

          {loading && (
            <p style={styles.loadingNote}>
              This may take 20-40 seconds on first run (AI model loading)
            </p>
          )}
        </div>
      ) : (
        // Results section
        <div style={styles.resultsSection}>
          <div style={styles.statsBar}>
            <div style={styles.statCard}>
              <div style={styles.statValue}>{result.papers_analyzed.length}</div>
              <div style={styles.statLabel}>Papers Analyzed</div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statValue}>{result.total_questions_extracted}</div>
              <div style={styles.statLabel}>Questions Found</div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statValue}>{result.total_groups}</div>
              <div style={styles.statLabel}>Unique Groups</div>
            </div>
          </div>

          <h2 style={styles.resultsTitle}>Ranked Questions by Priority</h2>
          <div style={styles.filterRow}>
            {["All", "High", "Medium", "Low"].map(priority => (
              <button
                key={priority}
                onClick={() => setFilter(priority)}
                style={{
                  ...styles.filterBtn,
                  ...(filter === priority ? styles.filterBtnActive : {})
                }}
              >
                {priority}
              </button>
            ))}
          </div>

          <div style={styles.questionList}>
            {result.ranked_questions
              .filter(q => filter === "All" || q.priority === filter)
              .map((question, index) => (
                <QuestionCard key={index} question={question} rank={index + 1} />
              ))}
          </div>

          <button onClick={handleReset} style={styles.resetBtn}>
            ↻ Analyze New Papers
          </button>
        </div>
      )}
    </div>
  );
}


const styles = {
  container: {
    maxWidth: "800px",
    margin: "0 auto",
    padding: "40px 20px",
    fontFamily: "system-ui, -apple-system, sans-serif",
  },
  title: {
    fontSize: "42px",
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: "10px",
  },
  subtitle: {
    textAlign: "center",
    color: "#666",
    marginBottom: "40px",
  },
  uploadSection: {
    border: "2px dashed #ccc",
    borderRadius: "8px",
    padding: "40px",
    textAlign: "center",
  },
  fileInput: {
    marginBottom: "20px",
  },
  fileList: {
    textAlign: "left",
    marginBottom: "20px",
  },
  fileItem: {
    display: "flex",
    justifyContent: "space-between",
    padding: "10px",
    border: "1px solid #eee",
    borderRadius: "4px",
    marginBottom: "8px",
  },
  removeBtn: {
    background: "#ff4444",
    color: "white",
    border: "none",
    padding: "4px 12px",
    borderRadius: "4px",
    cursor: "pointer",
  },
  error: {
    color: "#ff4444",
    padding: "10px",
    marginBottom: "20px",
    background: "#ffeeee",
    borderRadius: "4px",
  },
  analyzeBtn: {
    background: "#4CAF50",
    color: "white",
    border: "none",
    padding: "12px 32px",
    fontSize: "16px",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "bold",
  },
  btnDisabled: {
    background: "#ccc",
    cursor: "not-allowed",
  },
  loadingNote: {
    marginTop: "16px",
    color: "#666",
    fontSize: "14px",
  },
  resultsSection: {
    textAlign: "center",
    padding: "40px",
  },
  resetBtn: {
    marginTop: "20px",
    background: "#2196F3",
    color: "white",
    border: "none",
    padding: "10px 24px",
    borderRadius: "6px",
    cursor: "pointer",
  },
  statsBar: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "16px",
    marginBottom: "32px",
  },
  statCard: {
    background: "#f8f9fa",
    padding: "24px",
    borderRadius: "8px",
    textAlign: "center",
    border: "1px solid #e9ecef",
  },
  statValue: {
    fontSize: "36px",
    fontWeight: "bold",
    color: "#2196F3",
    marginBottom: "8px",
  },
  statLabel: {
    fontSize: "14px",
    color: "#666",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  resultsTitle: {
    fontSize: "28px",
    marginBottom: "24px",
    textAlign: "center",
  },
  questionList: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    marginBottom: "32px",
  },
  questionCard: {
    borderRadius: "8px",
    padding: "20px",
    border: "1px solid #ddd",
  },
  cardHeader: {
    display: "flex",
    gap: "16px",
  },
  rank: {
    fontSize: "20px",
    fontWeight: "bold",
    color: "#666",
    minWidth: "40px",
  },
  cardContent: {
    flex: 1,
  },
  cardMeta: {
    display: "flex",
    gap: "12px",
    marginBottom: "12px",
    flexWrap: "wrap",
  },
  priorityBadge: {
    color: "white",
    padding: "4px 12px",
    borderRadius: "20px",
    fontSize: "12px",
    fontWeight: "bold",
  },
  countBadge: {
    background: "#e9ecef",
    padding: "4px 12px",
    borderRadius: "20px",
    fontSize: "12px",
    color: "#495057",
  },
  questionText: {
    fontSize: "16px",
    lineHeight: "1.6",
    color: "#333",
    marginBottom: "12px",
  },
  variantToggle: {
    background: "none",
    border: "none",
    color: "#2196F3",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "600",
    padding: "0",
  },
  variantList: {
    marginTop: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  variantItem: {
    background: "rgba(255, 255, 255, 0.7)",
    padding: "12px",
    borderRadius: "6px",
    border: "1px solid rgba(0, 0, 0, 0.1)",
  },
  variantSource: {
    fontSize: "12px",
    color: "#666",
    fontWeight: "600",
    display: "block",
    marginBottom: "6px",
  },
  variantText: {
    fontSize: "14px",
    color: "#495057",
    margin: 0,
  },
  filterRow: {
  display: "flex",
  justifyContent: "center",
  gap: "12px",
  marginBottom: "24px",
  flexWrap: "wrap",
},

filterBtn: {
  padding: "8px 20px",
  borderRadius: "20px",
  border: "1px solid #ccc",
  background: "#f5f5f5",
  cursor: "pointer",
  fontWeight: "600",
  fontSize: "14px",
  transition: "all 0.2s ease",
  color: 'black'
},

filterBtnActive: {
  background: "#2196F3",
  color: "white",
  border: "1px solid #2196F3",
},
};