from helical.models.base_models import HelicalRNAModel
import anndata as ad
from helical.models.geneformer.geneformer_tokenizer import TranscriptomeTokenizer
from helical.models.geneformer.geneformer_config import GeneformerConfig
from helical.utils.mapping import map_gene_symbols_to_ensembl_ids
from typing import Optional
from helical_pdqueiros.io.logger import logger
from helical_pdqueiros.core.documents.data_document import DataDocument

class CellTypeAnnotationDataProcessor(HelicalRNAModel):
    """
    This is a copy of the Geneformer, but I've decoupled the data processing from the model so that we can run it in a distributed environment without reloading the model per worker.
    """

    def __init__(self, configurer: GeneformerConfig) -> None:
        super().__init__()
        self.configurer = configurer
        self.config = configurer.config
        self.files_config = configurer.files_config
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

    # TODO Im not sure how ray handles pickling of the tokenizer, so we probably need large enough chunks to avoid overhead from loading tokenizer in multiple cores
    def process_data(self,
                     data_document: DataDocument,
                     gene_names: str = "index",
                     output_path: Optional[str] = None,
                     use_raw_counts: bool = True,
                 ):
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
        tokenized_dataset.save_to_disk(output_path)
        logger.info(f"Successfully processed {data_document} for Geneformer.")

