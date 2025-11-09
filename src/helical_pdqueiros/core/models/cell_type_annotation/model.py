
from helical.models.geneformer import Geneformer, GeneformerConfig
# dataset = load_dataset("helical-ai/yolksac_human", split="train[:10%]", trust_remote_code=True, download_mode="reuse_cache_if_exists")
# labels = dataset["LVL1"]



# ann_data = get_anndata_from_hf_dataset(dataset)
# print(ann_data)

# device = "cuda" if torch.cuda.is_available() else "cpu"
# model_config = GeneformerConfig(batch_size=10,device=device)
# geneformer = Geneformer(configurer=model_config)


from helical_pdqueiros.core.models.model import AbstractModel
import logging
from helical_pdqueiros.io.logger import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

class CellTypeAnnotationModel(AbstractModel):
    model = Geneformer
    model_config = GeneformerConfig


if __name__ == '__main__':
    pass
    # model_config = GeneformerConfig(batch_size=10,device=device)
    # base_model = Geneformer(configurer=model_config)
    # model = CellTypeAnnotationModel.load(model_config_settings={'batch_size': 10})

