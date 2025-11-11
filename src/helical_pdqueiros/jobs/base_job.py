from abc import abstractmethod


class BaseJob():
    task=None

    def run(self):
        try:
            self._run()
        except (KeyboardInterrupt,Exception) as e:
            self.task.s3_client.unlock_files_on_exception()
            raise e

    @abstractmethod
    def _run(self):
        pass
