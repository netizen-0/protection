import logging
import os
from flask import Flask

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/health")
def health() -> str:
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info("Starting Flask health server on port %s", port)
    app.run(host="0.0.0.0", port=port)
