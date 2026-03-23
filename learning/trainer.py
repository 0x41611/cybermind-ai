"""
CyberMind AI - Training Manager
Orchestrates self-learning from CTF writeups
"""
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from config import config
from utils.logger import get_logger
from utils.helpers import save_json, load_json

logger = get_logger("trainer")


class TrainingStats:
    """Tracks training progress and history"""

    def __init__(self):
        self.stats_file = config.DATA_DIR / "training_stats.json"
        self._data = self._load()

    def _load(self) -> Dict:
        data = load_json(self.stats_file)
        if data is None:
            data = {
                "total_writeups": 0,
                "total_chunks": 0,
                "last_trained": None,
                "training_history": [],
                "sources_count": {},
                "categories_count": {},
            }
        return data

    def save(self):
        save_json(self.stats_file, self._data)

    def record_training(self, writeups_count: int, chunks_count: int, duration: float):
        self._data["total_writeups"] += writeups_count
        self._data["total_chunks"] += chunks_count
        self._data["last_trained"] = datetime.now().isoformat()
        self._data["training_history"].append({
            "timestamp": datetime.now().isoformat(),
            "writeups": writeups_count,
            "chunks": chunks_count,
            "duration_seconds": round(duration),
        })
        # Keep only last 50 training runs
        self._data["training_history"] = self._data["training_history"][-50:]
        self.save()

    def get_summary(self) -> Dict:
        return {
            "total_writeups": self._data["total_writeups"],
            "total_chunks": self._data["total_chunks"],
            "last_trained": self._data.get("last_trained"),
            "training_runs": len(self._data["training_history"]),
        }

    @property
    def last_trained(self) -> Optional[datetime]:
        ts = self._data.get("last_trained")
        if ts:
            try:
                return datetime.fromisoformat(ts)
            except Exception:
                pass
        return None


class Trainer:
    """
    Manages the self-training process.
    Scrapes writeups and adds them to the knowledge base.
    """

    def __init__(self, rag_engine, on_progress: Optional[Callable] = None,
                 on_complete: Optional[Callable] = None):
        self.rag_engine = rag_engine
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.stats = TrainingStats()
        self._is_training = False
        self._auto_train_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def is_training(self) -> bool:
        return self._is_training

    def train(self, sources: str = "all", max_writeups: int = None,
              custom_url: Optional[str] = None) -> Dict:
        """
        Run training synchronously (call from thread).
        Returns training results.
        """
        if self._is_training:
            return {"error": "Training already in progress"}

        self._is_training = True
        start_time = time.time()
        total_chunks = 0
        total_writeups = 0

        try:
            from learning.writeup_scraper import WriteupScraper

            max_w = max_writeups or config.MAX_WRITEUPS_PER_SCRAPE

            scraper = WriteupScraper(on_progress=self._progress)

            if custom_url:
                # Scrape custom URL
                self._progress(f"Scraping custom URL: {custom_url}")
                writeup = scraper.scrape_custom_url(custom_url)
                writeups = [writeup] if writeup else []
            else:
                # Scrape from all sources
                writeups = scraper.scrape_all(max_total=max_w)

            self._progress(f"📚 Scraped {len(writeups)} writeups. Adding to knowledge base...")

            # Add to RAG
            def add_progress(current, total, title):
                self._progress(f"Embedding {current}/{total}: {title[:50]}...")

            chunks = self.rag_engine.add_writeups_batch(writeups, on_progress=add_progress)
            total_chunks = chunks
            total_writeups = len(writeups)

            duration = time.time() - start_time
            self.stats.record_training(total_writeups, total_chunks, duration)

            result = {
                "success": True,
                "writeups_scraped": total_writeups,
                "chunks_added": total_chunks,
                "duration": round(duration),
            }

            self._progress(
                f"✅ Training complete! Added {total_chunks} knowledge chunks "
                f"from {total_writeups} writeups in {round(duration)}s"
            )

            if self.on_complete:
                self.on_complete(result)

            return result

        except Exception as e:
            logger.error(f"Training error: {e}")
            result = {"success": False, "error": str(e)}
            if self.on_complete:
                self.on_complete(result)
            return result

        finally:
            self._is_training = False

    def train_async(self, **kwargs) -> threading.Thread:
        """Run training in background thread"""
        thread = threading.Thread(
            target=self.train,
            kwargs=kwargs,
            daemon=True,
            name="CyberMind-Trainer"
        )
        thread.start()
        return thread

    def start_auto_training(self):
        """Start automatic periodic training"""
        if not config.AUTO_TRAIN:
            return

        if self._auto_train_thread and self._auto_train_thread.is_alive():
            return

        self._stop_event.clear()
        self._auto_train_thread = threading.Thread(
            target=self._auto_train_loop,
            daemon=True,
            name="CyberMind-AutoTrainer"
        )
        self._auto_train_thread.start()
        logger.info(f"Auto-training started (interval: {config.TRAIN_INTERVAL_HOURS}h)")

    def stop_auto_training(self):
        """Stop automatic training"""
        self._stop_event.set()

    def _auto_train_loop(self):
        """Background auto-training loop"""
        while not self._stop_event.is_set():
            # Check if it's time to train
            last = self.stats.last_trained
            if last is None or datetime.now() - last > timedelta(hours=config.TRAIN_INTERVAL_HOURS):
                logger.info("Auto-training: Starting scheduled training run")
                self.train()

            # Sleep for 30 minutes between checks
            self._stop_event.wait(timeout=1800)

    def get_stats(self) -> Dict:
        """Get training statistics"""
        stats = self.stats.get_summary()
        rag_stats = self.rag_engine.get_stats() if self.rag_engine else {}
        return {**stats, **rag_stats, "is_training": self._is_training}

    def _progress(self, message: str):
        logger.info(f"[Training] {message}")
        if self.on_progress:
            self.on_progress(message)
