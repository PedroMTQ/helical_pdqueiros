from helical_pdqueiros.io.s3_client import ClientS3


class BaseJob():
    def __init__(self):
        self.s3_client = ClientS3()

    def publish_metrics(self, ):
        pass