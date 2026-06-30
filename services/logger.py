from database.repository import add_log


class OrionLogger:
    def info(self, message):
        print("[INFO]", message)
        add_log("INFO", message)

    def warning(self, message):
        print("[WARNING]", message)
        add_log("WARNING", message)

    def error(self, message):
        print("[ERROR]", message)
        add_log("ERROR", message)