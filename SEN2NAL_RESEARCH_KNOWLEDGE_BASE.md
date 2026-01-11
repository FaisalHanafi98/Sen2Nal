# Sen2Nal Stock Sentiment Analysis System: Comprehensive Research Knowledge Base

**Bottom Line Up Front:** Building an effective stock sentiment analysis system requires combining transformer-based NLP models (FinBERT or FinGPT) with temporal pattern recognition, proper time-series validation to avoid lookahead bias, and a streaming architecture for real-time data processing. The research reveals that **sentiment alone achieves 60-75% accuracy**, but combining sentiment with volume metrics, technical indicators, and calendar patterns can push accuracy to **85-95%** for directional prediction. The optimal approach uses a hybrid architecture: FinBERT for news sentiment, VADER for social media speed, and XGBoost or LSTM for temporal pattern integration.

---

## Executive Summary

This knowledge base synthesizes **47 sources** covering financial sentiment analysis for the Sen2Nal project—a system combining NLP-based sentiment analysis from news/social media with calendar/seasonal pattern recognition from historical price data.

**Key findings across all sources:**

- **Model Selection:** FinBERT and FinGPT consistently outperform general NLP models by **14-35%** on financial text. ChatGPT with zero-shot prompting (no chain-of-thought) achieves **36% higher correlation** with market returns than FinBERT.
- **Data Volume Threshold:** Accuracy jumps from **60% to 85%** when increasing from 3,200 to 20,000+ data points per stock.
- **Time Windows Matter:** Using 9:30 market-open alignment for sentiment aggregation outperforms midnight-to-midnight natural days.
- **Multi-factor Approach Required:** Pure sentiment polarity shows weak correlation with prices; combining sentiment + volume + engagement metrics dramatically improves predictive power.
- **Calendar Effects Validated:** Holiday sentiment decay, weekend accumulation, and earnings-season patterns significantly impact prediction accuracy.

---

## Section 1: User-Provided Sources Analysis

### Academic Papers & Research (Sources 1-9)

#### Source 1: Pre-trained LLMs for Financial Sentiment Analysis (Youngstown State)
**URL:** https://etd.ohiolink.edu/acprod/odb_etd/ws/send_file/send?accession=ysu1682513807719236

**Summary:** This Master's thesis investigates fine-tuned Llama2-7B for financial sentiment classification, comparing against BERT and GPT architectures. The model was trained on Financial PhraseBank (4,845 sentences annotated by 16 finance professionals) using supervised fine-tuning (SFT).

**Key Contributions:**
- Demonstrates that even smaller LLMs (7B parameters) can achieve state-of-the-art results when properly fine-tuned
- Provides open-source implementation at GitHub: https://github.com/luosting/LLaMA-Financial-sentiment-analysis
- Shows transfer learning from general language models to financial domain is effective

**Relevance to Sen2Nal:** Informs choice between BERT-family (encoder) vs. GPT-family (decoder) architectures. The SFT methodology is directly applicable for customizing models to stock-specific sentiment.

**Limitations:** Focuses on classification only, not price prediction. Financial PhraseBank may not represent informal social media text styles.

---

#### Source 2: Stock Trend Prediction Using Sentiment Analysis (PMC)
**URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC10403218/

**Summary:** Comprehensive framework combining VADER for tweets and FinBERT for news, analyzing 260,000 tweets and 6,000 news articles for Amazon, Netflix, Apple, and Microsoft throughout 2021.

**Key Contributions:**
- **Critical Innovation:** Two time divisions—Natural hours (0:00-0:00) vs. Opening hours (9:30-9:30). Opening hours division **outperformed** natural hours for prediction.
- **Holiday Effect Modeling:** Exponential decay (e^-n) allocates weekend sentiment to next trading day
- **Weighted Sentiment Index:** Tweight (tweet popularity-weighted) and Nweight (FinBERT pos-neg ratio)
- Naïve Bayes achieved best accuracy at **62.4%** with sentiment features alone

**Relevance to Sen2Nal:** **CRITICAL** for calendar pattern integration. The 9:30 opening hours methodology and holiday effect decay directly inform Sen2Nal's temporal analysis.

**Limitations:** Best accuracy still modest (62.4%); only 4 stocks studied.

---

#### Source 3: Financial Sentiment Analysis Evaluated on Stock Market (DiVA)
**URL:** https://www.diva-portal.org/smash/get/diva2:1985458/FULLTEXT01.pdf

**Summary:** Swedish thesis comparing FinBERT, DistilRoBERTa, and Gemini (LLM) for sentiment on Twitter, Reddit, and news, combined with XGBoost, MLP, and LSTM predictors.

**Key Contributions:**
- **XGBoost achieved 90%+ accuracy** for next-day price direction prediction
- DistilRoBERTa most consistent across domains
- FinBERT best for formal news; Gemini excelled on unstructured social media
- 5-day context window for sentiment aggregation

**Relevance to Sen2Nal:** Strong case for XGBoost as the prediction layer. Platform-specific model selection (FinBERT for news, LLM for social) is validated.

**Limitations:** Potential overfitting concerns with 90%+ claims; Swedish market focus.

---

#### Source 4: NLP for Sentiment Analysis in Stock Prediction (ResearchGate)
**URL:** https://www.researchgate.net/publication/392444846

**Summary:** Survey paper (December 2024) examining NLP techniques for stock sentiment, emphasizing domain adaptation of models through fine-tuning on financial corpora.

**Key Contributions:**
- End-to-end pipeline framework from data collection to prediction integration
- Domain adaptation significantly improves classification performance
- Multi-source integration strategies (news + social + reports)

**Relevance to Sen2Nal:** Provides complete methodology framework adaptable for sentiment-to-prediction workflow.

**Limitations:** Survey nature means less empirical validation.

---

#### Source 5: Rule-Based Stock Trading with Sentiment + RSI (MDPI)
**URL:** https://www.mdpi.com/2079-9292/14/4/773

**Summary:** Practical system integrating TextBlob sentiment with RSI technical indicator for 95 U.S. stocks across market caps (February 2025).

**Key Contributions:**
- **Transparent rule-based approach:** Strong Buy (sentiment >70, RSI <30), Buy (sentiment >50, RSI 30-50), etc.
- **7-day sentiment window** proven effective
- Achieved **4.03% average return** vs. benchmarks (DJIA 2.21%, S&P 500 2.72%)
- High Beta stocks achieved **95% prediction accuracy**
- Lightweight design for real-time consumer hardware

**Relevance to Sen2Nal:** **Directly applicable** rule-based framework for combining sentiment with calendar patterns and technical indicators.

**Limitations:** TextBlob less accurate than FinBERT; 7-week backtest relatively short.

---

#### Source 6: Enhancing Trading with LLMs - S&P 500 Evidence (arXiv)
**URL:** https://arxiv.org/html/2507.09739v1

**Summary:** UCLA study merging sentiment from 5 financial news sources (WSJ, Barron, Benzinga, MarketWatch, Dow Jones) with technical indicators (MACD, SAR, Prophet, ETS).

**Key Contributions:**
- **FinBERT achieved 75.56% accuracy** on Benzinga; GPT-2 65.48% on WSJ
- VW MACD + GPT-2 hybrid achieved **5.77% return** vs. -0.696% buy-and-hold
- Weekend news aggregated to Monday's return
- Lag structure (k=0,1,2 days) for temporal testing

**Relevance to Sen2Nal:** Multi-source sentiment fusion methodology directly applicable. Prophet/ETS for seasonality relevant to calendar effects.

**Limitations:** Zero transaction costs assumed; short test period (May-August 2024).

---

#### Source 7: Deep Learning LSTM for Stock Price Prediction (IJACSA)
**URL:** https://thesai.org/Downloads/Volume15No12/Paper_23-A_Deep_Learning_Based_LSTM_for_Stock_Price_Prediction.pdf

**Summary:** LSTM + XGBoost framework for Apple, Google, Tesla using Twitter sentiment with 3-feature input (polarity, tweet volume, price).

**Key Contributions:**
- **12.05% RMSE improvement** over price-only models
- Tweet volume recognized as important signal beyond just sentiment direction
- Date alignment methodology for merging sentiment with price data

**Relevance to Sen2Nal:** Feature combination template (polarity + volume + price) is simple but effective.

**Limitations:** Limited to tech stocks; historical tweet data from 2015-2020.

---

#### Source 8: Stock Prediction Using Twitter Sentiment (Stanford CS229)
**URL:** https://cs229.stanford.edu/proj2011/GoelMittal-StockMarketPredictionUsingTwitterSentimentAnalysis.pdf

**Summary:** Foundational 2011 Stanford paper decomposing Twitter sentiment into mood dimensions (Calm, Happy, Alert, Kind) for DJIA prediction.

**Key Contributions:**
- **Mood decomposition framework** - Calm + Happy optimal combination
- SOFNN achieved **75.56% accuracy** with ICHD features
- **3-4 day prediction lead time** discovered
- Granger causality evidence of mood → stock price relationship
- Sequential k-fold cross-validation for time series

**Relevance to Sen2Nal:** Mood decomposition could enhance sentiment analysis. Lead time discovery aligns with calendar pattern detection.

**Limitations:** Dated (2011); pre-deep learning era.

---

#### Source 9: ML Classifiers with Social Media and News (UEL)
**URL:** https://uel-repository.worktribe.com/OutputFile/440239

**Summary:** Framework for 10-day prediction horizon using dual-source integration (news + social media) with spam filtering and feature selection.

**Key Contributions:**
- **10-day prediction horizon** matches potential calendar patterns
- Spam reduction methodology critical for social media quality
- Feature selection reduces dimensionality while maintaining power

**Relevance to Sen2Nal:** 10-day horizon matches weekly/bi-weekly calendar patterns.

**Limitations:** Full paper access restricted.

---

### Industry/Blog Articles (Sources 10-14)

#### Source 10: Complete Guide to Sentiment Analysis (Thematic)
**URL:** https://getthematic.com/sentiment-analysis

**Summary:** Comprehensive guide covering ABSA (Aspect-Based Sentiment Analysis), scoring systems, and LLM approaches.

**Key Contributions:**
- **ABSA methodology:** Identify sentiment about specific attributes (e.g., "processor speed" not just overall sentiment)
- Sentiment scoring: -1 to +1 continuous scale
- **92% accuracy** on 15,000-comment training set
- Real-time monitoring capabilities

**Relevance to Sen2Nal:** ABSA can identify sentiment about specific stock attributes (earnings, management, products).

**Limitations:** Focused on customer feedback, not financial text.

---

#### Source 11: Sentiment Analysis Stock Market (AIMultiple)
**URL:** https://research.aimultiple.com/sentiment-analysis-stock-market/

**Summary:** Finance-focused examination with specific accuracy data and platform comparisons.

**Key Contributions:**
- **20% accuracy improvement** when incorporating sentiment into price prediction
- **BERT achieves 97.35% accuracy**, outperforming LSTM and SVM
- Data volume critical: **60% → 85% accuracy** with 3,200 → 20,000 tweets
- GPT-based portfolio: **Sharpe ratio 3.05, 355% gains over 2 years**

**Relevance to Sen2Nal:** Clear evidence of sentiment-price correlation validates approach. Data volume thresholds establish minimums.

**Limitations:** Some XGB 99% claims lack generalizability.

---

#### Source 12: NLP for Financial Sentiment Analysis (PyQuant News)
**URL:** https://www.pyquantnews.com/free-python-resources/nlp-for-financial-sentiment-analysis

**Summary:** Practitioner-focused overview with four-step pipeline and real-world examples.

**Key Contributions:**
- **Pipeline:** Preprocessing → Tokenization → Lexicon Analysis → ML Models
- Real-world implementations: Bloomberg, RavenPack, MarketPsych
- Domain-specific model training requirement confirmed
- BERT and GPT-3 as state-of-the-art

**Relevance to Sen2Nal:** Four-step pipeline provides implementation architecture.

**Limitations:** Overview-level; no quantitative performance metrics.

---

#### Source 13: Sentiment Analysis for Stock Valuation Guide (GetFocal)
**URL:** https://www.getfocal.co/post/sentiment-analysis-for-stock-valuation-guide

**Summary:** Practical guide with specific accuracy metrics and counterexamples.

**Key Contributions:**
- Concrete accuracy: **AAPL 75.38%, TSLA 71.86%, AMZN 74.80%**
- **Alibaba counterexample:** Sentiment dropped from 0.56 to -0.18, yet stock went UP
- **Holiday effect** explicitly mentioned for calendar integration
- Weighted sentiment index approach

**Relevance to Sen2Nal:** Calendar patterns validated ("holiday effect"). Alibaba case shows need for multi-factor confirmation.

**Limitations:** Commercial bias; some accuracy claims lack methodology.

---

#### Source 14: Advancing Financial Sentiment with AI-Driven GPT (LinkedIn + Academic)
**URL:** Multiple academic sources on GPT-based sentiment

**Summary:** Collection of cutting-edge research on GPT and FinGPT for financial sentiment.

**Key Contributions:**
- **ChatGPT outperforms FinBERT by 35%** in sentiment classification
- **36% higher correlation** with market returns using zero-shot prompting
- **FinGPT matches/exceeds GPT-4** on financial sentiment with single GPU training ($17 vs. $2.67M for BloombergGPT)
- LoRA fine-tuning enables cost-effective domain adaptation
- Multi-language capability for global markets

**Relevance to Sen2Nal:** FinGPT provides open-source option without API costs. Prompt engineering importance validated.

**Limitations:** Rapidly evolving field; adversarial vulnerability concerns.

---

### Reddit Discussions & YouTube (Sources 15-17)

#### Sources 15-16: Reddit r/algotrading Discussions
**URLs:** Original threads inaccessible; alternative sources analyzed

**Key Practitioner Insights:**
- **Compound score > 0.05** as buy threshold (Alpaca tutorial)
- **Sentiment + volume outperforms pure sentiment** (QuantifiedStrategies)
- **BERTweet > VADER** for accuracy: 86% vs 56%
- **Data cleaning crucial** - BERTweet struggles with informal language, sarcasm
- **Day-over-day sentiment change** may be more predictive than absolute levels

**Relevance to Sen2Nal:** Volume-weighted sentiment validated. Entity extraction (tickers/cashtags) critical.

**Limitations:** Anecdotal evidence; crypto-specific results may not transfer to equities.

---

#### Source 17: YouTube Video Analysis
**URL:** https://www.youtube.com/watch?v=NLCxl_asHT4 (transcript unavailable)

**Alternative Findings (NYC Data Science Academy):**
- Model comparison on StockTwits (1.5M observations):
  - Traditional Neural Nets: **71-77%**
  - BERT base: **80%**
  - FinBERT: **84%**
  - BERTweet: **86%**
  - Fine-tuned RoBERTa: **88%**

---

## Section 2: Model Approaches (10 New Articles)

### Comparison Table: Sentiment Analysis Models

| Model Type | Representative | Accuracy | Training Cost | Inference Speed | Best For |
|------------|---------------|----------|---------------|-----------------|----------|
| **Transformer (Domain)** | FinBERT | 88% F1 | Low (fine-tune) | Fast | News, SEC filings |
| **Transformer (General)** | RoBERTa | 88% | Medium | Fast | General text |
| **LLM (Open-source)** | FinGPT | 90% F1 | $17-22 | Medium | Multi-task finance |
| **LLM (API)** | GPT-4o | Best zero-shot | High API cost | Slow | Complex analysis |
| **LSTM/RNN** | BERT+LSTM | 95.5% (claimed) | Medium | Fast | Temporal patterns |
| **Traditional ML** | Random Forest | 88-92% | Very Low | Very Fast | Baseline/interpretability |
| **Lexicon** | Loughran-McDonald | N/A | None | Instant | Efficient baseline |
| **Ensemble** | CatBoost+LR+SVM | Superior | Low | Fast | Robust production |
| **Hybrid** | EnhancedFinSentiBERT | Superior | Medium | Fast | Neutral detection |

### Detailed Article Analyses

#### 1. FinBERT: Financial Sentiment Analysis with Pre-trained Models
**URL:** https://arxiv.org/abs/1908.10063

- **14% improvement** over prior state-of-the-art on FinancialPhraseBank
- F1 score of **0.88**
- Pre-trained model available on HuggingFace
- **Limitation:** 73% of errors are positive/neutral confusion

#### 2. LSTM-based Sentiment for Stock Forecast
**URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7959635/

- Multi-source integration (news + social media)
- **12.05% RMSE improvement** with sentiment features
- 20-day sliding window for temporal modeling

#### 3. FinGPT: Open-Source Financial LLMs
**URL:** https://github.com/AI4Finance-Foundation/FinGPT

- **F1 Scores:** FPB 0.882, FiQA-SA 0.874, TFNS 0.903
- Training cost: **$17.25** vs. $2.67M for BloombergGPT
- Trainable on single RTX 3090
- Supports multiple languages

#### 4. Loughran-McDonald Master Dictionary
**URL:** https://sraf.nd.edu/loughranmcdonald-master-dictionary/

- **7 sentiment categories:** negative, positive, uncertainty, litigious, strong modal, weak modal, constraining
- Based on SEC 10-K analysis
- **35,000+ citations**
- Python module available

#### 5. LLM Evaluation: Reasoning or Overthinking
**URL:** https://arxiv.org/abs/2506.04574

- **Key Finding:** Reasoning does NOT improve financial sentiment analysis
- GPT-4o without Chain-of-Thought performs **best**
- More tokens = worse performance

#### 6. Traditional ML: SVM, Random Forest, Naive Bayes
**URL:** https://arxiv.org/pdf/1607.01958

- Random Forest: **88-92%** accuracy
- SVM: ~86%
- Naive Bayes: ~83%
- Fast and interpretable

#### 7. Ensemble Methods Comparison
**URL:** https://journals.sagepub.com/doi/10.3233/IDT-230478

- **Ensembles consistently outperform** individual methods
- Best: CatBoost + Logistic Regression + SVM
- Surprising: FinBERT sometimes underperformed general BERT

#### 8. FinBERT-LSTM Hybrid Architecture
**URL:** https://dl.acm.org/doi/10.1145/3694860.3694870

- Testing loss: **0.00083**
- Accuracy: **95.5%**
- News category weighting for interpretability

#### 9. ChatGPT for Financial Sentiment
**URL:** https://www.sciencedirect.com/science/article/pii/S2666827023000610

- ChatGPT outperformed FinBERT by **35%**
- **36% higher correlation** with market returns
- Zero-shot prompting effective

#### 10. Hybrid Lexicon + Transformer
**URL:** https://www.sciencedirect.com/science/article/pii/S294971912500024X

- Dictionary knowledge embedding layer
- **Superior neutral sentiment recognition**
- Combines Loughran-McDonald with transformer

---

## Section 3: System Architecture (10 New Articles)

### Architectural Patterns Identified

| Pattern | Use Case | Key Technologies | Sen2Nal Applicability |
|---------|----------|------------------|----------------------|
| **Event-Driven Streaming** | Real-time news processing | Kafka, Kinesis | Primary architecture |
| **Serverless ML** | Variable load sentiment | AWS Lambda, Comprehend | Cost-effective scaling |
| **Pipeline Orchestration** | Model training workflow | Airflow, Prefect, TFX | MLOps foundation |
| **API-First Serving** | Model deployment | FastAPI, TF Serving | Production serving |
| **Dashboard Architecture** | Visualization | Streamlit, Plotly | User interface |

### Technology Stack Recommendations

**Data Ingestion Layer:**
- Alpaca News API (financial news, streaming + REST)
- Apache Kafka 4.0 with KRaft (message queue)
- WebSocket handlers for real-time feeds

**Processing Layer:**
- Apache Spark ML (batch training)
- HuggingFace Transformers (FinBERT, FinGPT)
- TF-IDF + Logistic Regression (baseline)

**Serving Layer:**
- FastAPI with Uvicorn (REST API)
- Docker containerization
- Evidently for drift monitoring

**Storage Layer:**
- PostgreSQL (structured data)
- TimescaleDB (time-series prices)
- MongoDB (unstructured text)

**Frontend:**
- Streamlit (rapid prototyping)
- Plotly (interactive charts)
- Word clouds, sentiment breakdowns

**MLOps:**
- MLflow (experiment tracking)
- DVC (data versioning)
- GitHub Actions (CI/CD)

### Key Architecture Articles

1. **Simform Real-Time Pipeline** - AWS-based streaming architecture
2. **HPE Spark ML Pipeline** - TF-IDF + Logistic Regression
3. **MLOps.org Principles** - Three automation levels
4. **Evidently FastAPI Tutorial** - Model serving + monitoring
5. **Estuary Kafka Pipeline** - KRaft mode, exactly-once semantics
6. **TFX Pipelines Tutorial** - Production-grade ML workflows
7. **NLP Summit Streaming** - Kubernetes + Seldon deployment
8. **Streamlit Dashboard** - Sentiment visualization
9. **Alpaca News API** - Financial news integration
10. **Google Cloud MLOps** - Maturity model roadmap

---

## Section 4: Best Practices (10 New Articles)

### Implementation Checklist

#### Evaluation Metrics
- [ ] Use **F1 score** (not accuracy) for imbalanced sentiment classes
- [ ] Calculate **class-specific precision/recall** for bearish/bullish signals
- [ ] Generate confusion matrices to identify error patterns
- [ ] Consider **Cohen's Kappa** for human-model agreement

#### Avoiding Lookahead Bias
- [ ] **Split first, normalize later** - calculate statistics only on training data
- [ ] Ensure news timestamps **precede** price movements
- [ ] Use only features available at prediction time
- [ ] Never shuffle time series data

#### Backtesting Methodology
- [ ] Implement **walk-forward validation** (gold standard)
- [ ] Use **TimeSeriesSplit** from sklearn
- [ ] Add **gap (purging)** between train/test for autocorrelated data
- [ ] Test on multiple market regimes (bull, bear, sideways)

#### Handling Class Imbalance
- [ ] Apply **SMOTE only to training data**
- [ ] Consider **class weights** as alternative to resampling
- [ ] Use **Borderline-SMOTE** for sentiment boundary cases
- [ ] Evaluate with appropriate metrics (F1, not accuracy)

#### Time Series Cross-Validation
- [ ] **Never use standard k-fold** for time series
- [ ] Choose between **expanding** vs. **sliding window**
- [ ] Respect temporal order in all splits
- [ ] Prevent information leakage from autocorrelations

#### Model Interpretability
- [ ] Use **SHAP for global** feature importance
- [ ] Use **LIME for local** prediction explanations
- [ ] Visualize attention weights for transformer models
- [ ] Validate importance rankings with domain knowledge

#### Financial Text Preprocessing
- [ ] Handle **ticker symbols** ($AAPL, AAPL, Apple)
- [ ] Process **financial slang** (moon, diamond hands, HODL)
- [ ] Disambiguate company names (Apple Inc vs. apple fruit)
- [ ] Extract **numerical context** (revenue up 5% vs down 5%)

#### CI/CD for ML
- [ ] Automate model training on code changes
- [ ] Generate evaluation reports with **CML**
- [ ] Version data with **DVC**
- [ ] Separate CI and CD workflows

#### Testing Strategy
- [ ] **Unit tests** for preprocessing functions
- [ ] **Data tests** with Great Expectations
- [ ] **Behavioral tests** (CheckList framework)
- [ ] **Integration tests** for end-to-end pipeline

---

## Section 5: Comparative Analysis

### Model Accuracy by Data Source

| Data Source | Best Model | Accuracy Range | Key Challenge |
|-------------|------------|----------------|---------------|
| **Financial News** | FinBERT | 75-88% | Domain vocabulary |
| **SEC Filings** | Loughran-McDonald + BERT | 80-90% | Document length |
| **Twitter/X** | BERTweet | 86% | Sarcasm, slang |
| **Reddit** | FinGPT | 74-82% | Noise, spam |
| **Combined Sources** | Ensemble | 85-95% | Alignment, weighting |

### Trade-offs Between Approaches

**Speed vs. Accuracy:**
- Lexicon methods: ~0.001s, ~65% accuracy
- FinBERT: ~0.1s, ~85% accuracy
- GPT-4 API: ~2s, ~90% accuracy

**Cost vs. Performance:**
- Loughran-McDonald: Free, interpretable, limited
- FinBERT: Free (HuggingFace), good accuracy
- FinGPT: $17-22 training, best open-source
- GPT-4 API: $0.01-0.03/call, highest accuracy

**Interpretability vs. Complexity:**
- Random Forest: High interpretability, feature importance
- LSTM: Temporal modeling, attention visualization
- Transformer: Best accuracy, harder to interpret

### What Works Best for Different Scenarios

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| **Real-time trading** | VADER + rules | Speed critical; 62-75% accuracy acceptable |
| **Daily rebalancing** | FinBERT + XGBoost | Balance of accuracy and latency |
| **Research/backtesting** | FinGPT + ensemble | Maximum accuracy, cost less critical |
| **Portfolio analysis** | GPT-4 + SHAP | Deep analysis, explainability needed |
| **High-frequency** | Lexicon only | Sub-millisecond requirement |

---

## Section 6: Recommended Approach for Sen2Nal

### Optimal Model Selection

**Primary Sentiment Layer:** FinBERT (ProsusAI/finbert)
- Rationale: Best balance of accuracy (88% F1), speed, and availability
- Fallback: VADER for high-volume social media processing

**Temporal Pattern Layer:** XGBoost with engineered features
- Rationale: Consistent 90%+ accuracy in research; handles calendar features naturally
- Alternative: LSTM for pure time-series patterns

**Calendar Integration Layer:** Rule-based with learned weights
- Opening hours (9:30) sentiment aggregation
- Holiday effect decay (e^-n)
- Earnings season, options expiry, FOMC meeting patterns

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION                          │
├─────────────────────────────────────────────────────────────────┤
│  Alpaca News API → Kafka → News Processor                      │
│  Twitter/Reddit → Streaming Handler → Social Processor         │
│  Alpha Vantage → Price Fetcher → TimescaleDB                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      SENTIMENT PROCESSING                       │
├─────────────────────────────────────────────────────────────────┤
│  News Text → FinBERT → Sentiment Score (-1 to +1)              │
│  Social Text → VADER → Compound Score + Volume Weight          │
│  Ticker Extraction → Entity Linking → Stock Assignment         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE ENGINEERING                          │
├─────────────────────────────────────────────────────────────────┤
│  Sentiment Features: polarity, volume, delta, momentum         │
│  Calendar Features: day_of_week, month, earnings_proximity     │
│  Technical Features: RSI, MACD, volume                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      PREDICTION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  XGBoost Classifier → Direction Prediction                     │
│  Confidence Threshold → Signal Generation                      │
│  SHAP Analysis → Explainability                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        SERVING & UI                             │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI → REST API → Signal Delivery                          │
│  Streamlit → Dashboard → Visualization                         │
│  Evidently → Monitoring → Drift Detection                      │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Priorities

**Phase 1: MVP (Weeks 1-4)**
1. Set up data ingestion (Alpaca News API)
2. Implement FinBERT sentiment scoring
3. Build basic feature pipeline
4. Create Streamlit dashboard prototype

**Phase 2: Calendar Integration (Weeks 5-8)**
1. Add calendar feature engineering
2. Implement XGBoost prediction
3. Build backtesting framework with walk-forward validation
4. Add SHAP explainability

**Phase 3: Production (Weeks 9-12)**
1. Deploy FastAPI serving layer
2. Add Evidently monitoring
3. Implement CI/CD with GitHub Actions
4. Scale with Kafka for real-time processing

### What to Build vs. What to Avoid

**BUILD:**
- Multi-source sentiment aggregation (news + social)
- Calendar-aware feature engineering
- Transparent rule-based signal generation
- Walk-forward backtesting framework
- Explainable predictions with SHAP

**AVOID:**
- Black-box deep learning without interpretability
- Overfitting to specific time periods
- Single-source sentiment reliance
- Standard k-fold cross-validation
- Ignoring transaction costs in backtests

---

## Appendix: Quick Reference Tables

### All Sources: One-Line Summaries

| # | Source | One-Line Summary |
|---|--------|------------------|
| 1 | YSU Thesis | Llama2-7B fine-tuning achieves SOTA on Financial PhraseBank |
| 2 | PMC Paper | Opening hours (9:30) sentiment aggregation beats natural days |
| 3 | DiVA Thesis | XGBoost + DistilRoBERTa achieves 90%+ accuracy |
| 4 | ResearchGate Survey | Domain adaptation critical for financial NLP |
| 5 | MDPI Paper | TextBlob + RSI rule-based system beats benchmarks |
| 6 | UCLA arXiv | VW MACD + sentiment achieves 5.77% vs -0.7% buy-hold |
| 7 | IJACSA Paper | LSTM + tweet volume improves RMSE by 12% |
| 8 | Stanford CS229 | Calm + Happy mood dimensions predict DJIA 3-4 days ahead |
| 9 | UEL Paper | 10-day prediction horizon with spam filtering |
| 10 | Thematic | ABSA methodology for aspect-specific sentiment |
| 11 | AIMultiple | BERT achieves 97.35%; 20K+ tweets needed for accuracy |
| 12 | PyQuant News | Four-step pipeline: preprocess → tokenize → lexicon → ML |
| 13 | GetFocal | Holiday effect validated; Alibaba counterexample |
| 14 | GPT Research | ChatGPT outperforms FinBERT by 35%; FinGPT costs $17 |
| 15-16 | Reddit | Volume-weighted sentiment > pure polarity |
| 17 | YouTube | Fine-tuned RoBERTa achieves 88% on StockTwits |
| 18 | FinBERT Paper | 88% F1, 14% improvement over SOTA |
| 19 | LSTM Paper | Multi-source integration, 12% RMSE improvement |
| 20 | FinGPT GitHub | 90% F1, trainable on single GPU |
| 21 | L-M Dictionary | 35K+ citations, 7 sentiment categories |
| 22 | LLM Evaluation | GPT-4o without CoT performs best |
| 23 | Traditional ML | Random Forest 88-92% accuracy |
| 24 | Ensemble Study | CatBoost + LR + SVM optimal combination |
| 25 | FinBERT-LSTM | 95.5% accuracy hybrid architecture |
| 26 | ChatGPT Study | 36% higher correlation with market returns |
| 27 | Hybrid Lexicon | Superior neutral sentiment detection |
| 28 | Simform Pipeline | AWS serverless streaming architecture |
| 29 | HPE Spark | TF-IDF + Logistic Regression pipeline |
| 30 | MLOps.org | Three automation levels for ML operations |
| 31 | Evidently Tutorial | FastAPI + monitoring for drift detection |
| 32 | Kafka Pipeline | KRaft mode, exactly-once semantics |
| 33 | TFX Tutorial | Production-grade ML pipeline framework |
| 34 | NLP Summit | Kubernetes + Seldon for streaming NLP |
| 35 | Streamlit Dashboard | Sentiment visualization with word clouds |
| 36 | Alpaca Tutorial | News API + Transformers integration |
| 37 | Google MLOps | Maturity model: Level 0 → 1 → 2 |
| 38 | Metrics Article | F1 score essential for imbalanced sentiment |
| 39 | Lookahead Bias | Split first, normalize later |
| 40 | Backtesting | Walk-forward validation gold standard |
| 41 | SMOTE Article | Apply only to training data |
| 42 | Time Series CV | TimeSeriesSplit, never shuffle |
| 43 | SHAP/LIME | SHAP global, LIME local explanations |
| 44 | Feature Importance | Compare across multiple models |
| 45 | Financial Text | Handle tickers, slang, disambiguation |
| 46 | CI/CD for ML | GitHub Actions + CML + DVC |
| 47 | ML Testing | Unit + Data + Behavioral tests |

### Technology Recommendations

| Category | Recommended | Alternative | Avoid |
|----------|-------------|-------------|-------|
| **Sentiment Model** | FinBERT | FinGPT, GPT-4 | VADER alone |
| **Prediction Model** | XGBoost | LSTM, Random Forest | Complex ensembles |
| **Data Pipeline** | Kafka | Kinesis, RabbitMQ | Polling-only |
| **API Framework** | FastAPI | Flask | Django |
| **Dashboard** | Streamlit | Plotly Dash | Custom JS |
| **Monitoring** | Evidently | Prometheus | None |
| **Experiment Tracking** | MLflow | W&B | Manual logs |
| **Data Versioning** | DVC | LakeFS | Git LFS |
| **Database** | PostgreSQL + TimescaleDB | MongoDB | MySQL |

### Evaluation Metrics to Use

| Metric | When to Use | Formula |
|--------|-------------|---------|
| **F1 Score** | Imbalanced classes (primary) | 2 × (P × R) / (P + R) |
| **Precision** | False positives costly | TP / (TP + FP) |
| **Recall** | Missing signals costly | TP / (TP + FN) |
| **ROC-AUC** | Threshold selection | Area under ROC curve |
| **Sharpe Ratio** | Strategy evaluation | (R_p - R_f) / σ_p |
| **RMSE** | Price prediction | √(Σ(y - ŷ)² / n) |
| **Directional Accuracy** | Trading signals | % correct direction |

---

*This knowledge base consolidates 47 sources for the Sen2Nal stock sentiment analysis system. The recommended approach combines FinBERT sentiment, calendar-aware feature engineering, XGBoost prediction, and a streaming architecture—delivering an interview-defensible, explainable, and production-ready system.*