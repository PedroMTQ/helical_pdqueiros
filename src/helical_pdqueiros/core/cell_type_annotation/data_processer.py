import logging

import anndata as ad
from helical.models.base_models import HelicalRNAModel
from helical.models.geneformer.geneformer_config import GeneformerConfig
from helical.models.geneformer.geneformer_tokenizer import TranscriptomeTokenizer
from helical.utils.mapping import map_gene_symbols_to_ensembl_ids
from retry import retry

from helical_pdqueiros.core.documents.data_document import DataDocument
from helical_pdqueiros.settings import DATASET_LABEL_NAME, LABEL_NAME, MODEL_NAME

logger = logging.getLogger(__name__)

class CellTypeAnnotationDataProcessor(HelicalRNAModel):
    """
    This is a copy of Helical's Geneformer, but I've decoupled the data processing from the model so that we can run it in a distributed environment without reloading the model per worker.
    """
    # There's some weird issue with Helical's setup
    @retry(tries=3, delay=2)
    def __init__(self) -> None:
        super().__init__()
        self.configurer = GeneformerConfig(model_name=MODEL_NAME)
        self.config = self.configurer.config
        self.files_config = self.configurer.files_config
        self.tokenizer = TranscriptomeTokenizer(
            custom_attr_name_dict=self.config["custom_attr_name_dict"],
            nproc=self.config["nproc"],
            model_input_size=self.config["input_size"],
            special_token=self.config["special_token"],
            gene_median_file=self.files_config["gene_median_path"],
            token_dictionary_file=self.files_config["token_path"],
            gene_mapping_file=self.files_config["ensembl_dict_path"],
        )

    def get_embeddings(self):
        # TODO the get_embedding should not be an abstractmethod if we decouple it
        return

    def process_data(self, data_document: DataDocument, output_path: str, gene_names: str = "index", use_raw_counts: bool = True):
        """
        Processes the data for the Geneformer model.

        Parameters
        ----------
        adata : AnnData
            The AnnData object containing the data to be processed. Geneformer uses Ensembl IDs to identify genes
            and currently supports only human genes. If the AnnData object already has an 'ensembl_id' column,
            the mapping step can be skipped.
        gene_names : str, optional, default="index"
            The column in `adata.var` that contains the gene names. If set to a value other than "ensembl_id",
            the gene symbols in that column will be mapped to Ensembl IDs using the 'pyensembl' package,
            which retrieves mappings from the Ensembl FTP server and loads them into a local database.
            - If set to "index", the index of the AnnData object will be used and mapped to Ensembl IDs.
            - If set to "ensembl_id", no mapping will occur.
            Special case:
                If the index of `adata` already contains Ensembl IDs, setting this to "index" will result in
                invalid mappings. In such cases, create a new column containing Ensembl IDs and pass "ensembl_id"
                as the value of `gene_names`.
        output_path : str, optional, default=None
            If specified, saves the tokenized dataset to the given output path.
        use_raw_counts : bool, optional, default=True
            Determines whether raw counts should be used.

        Returns
        -------
        Dataset
            The tokenized dataset in the form of a Huggingface Dataset object.
        """
        logger.debug(f"Processing {data_document} for Geneformer.")
        adata: ad.AnnData = data_document.data
        cell_types = list(adata.obs[LABEL_NAME])
        self.ensure_rna_data_validity(adata, gene_names, use_raw_counts)
        # map gene symbols to ensemble ids if provided
        if gene_names != "ensembl_id":
            if (adata.var[gene_names].str.startswith("ENS").all()) or (
                adata.var[gene_names].str.startswith("None").any()
            ):
                message = (
                    "It seems an anndata with 'ensemble ids' and/or 'None' was passed. "
                    "Please set gene_names='ensembl_id' and remove 'None's to skip mapping."
                )
                logger.info(message)
                raise ValueError(message)
            adata = map_gene_symbols_to_ensembl_ids(adata, gene_names)

            if adata.var["ensembl_id"].isnull().all():
                message = "All gene symbols could not be mapped to Ensembl IDs. Please check the input data."
                logger.info(message)
                raise ValueError(message)

        tokenized_cells, cell_metadata = self.tokenizer.tokenize_anndata(adata)
        tokenized_dataset = self.tokenizer.create_dataset(tokenized_cells=tokenized_cells,
                                                          cell_metadata=cell_metadata,
                                                          use_generator=False)
        tokenized_dataset = tokenized_dataset.add_column(DATASET_LABEL_NAME, cell_types)
        # TODO
        # we could add integration with S3 directly -> https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem
        tokenized_dataset.save_to_disk(output_path)
        logger.info(f"Successfully processed {data_document} for Geneformer")
        return output_path


if __name__ == '__main__':
    task = CellTypeAnnotationDataProcessor()
    data_doc = DataDocument(file_path='/home/pedroq/workspace/helical_pdqueiros/tests/dataset.h5ad')
    task.process_data(data_document=data_doc, output_path='/home/pedroq/workspace/helical_pdqueiros/tmp/test.h5ad')
