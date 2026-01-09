class ChromaTextSplitter(object):
    """
    Split text into chunks using recursive character splitting.

    This is a custom implementation that replicates the functionality of
    langchain_text_splitters.RecursiveCharacterTextSplitter without external dependencies.

    The splitter recursively splits text by a set of separators:
    - First tries to split by paragraph breaks (\\n\\n)
    - Then by line breaks (\\n)
    - Then by spaces
    - Finally by individual characters

    This approach preserves semantic structure while ensuring chunks don't exceed
    the specified chunk_size.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
    ):
        """
        Initialize the text splitter.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to use for splitting. Defaults to
                       ["\\n\\n", "\\n", " ", ""] (paragraph, line, space, character)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> list[str]:
        """
        Split text into chunks.

        Args:
            text: The text to split

        Returns:
            A list of text chunks, each with length <= chunk_size
        """
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """
        Recursively split text by separators.

        Args:
            text: The text to split
            separators: List of separators to try, in order

        Returns:
            A list of text chunks
        """
        good_splits = []
        separator = separators[-1]

        # Try each separator in order
        for i, sep in enumerate(separators):
            if sep == "":
                # Empty separator means split by character
                splits = list(text)
            else:
                splits = text.split(sep)

            # Check if we found good splits with this separator
            if len(splits) > 1:
                separator = sep
                break

        # Now go through the splits and merge them
        good_splits = []
        separator_to_use = separator

        for s in splits:
            if len(s) < self.chunk_size:
                good_splits.append(s)
            else:
                # This split is too large, need to recursively split it
                if good_splits:
                    # Merge the good splits we have so far
                    merged_text = self._merge_splits(good_splits, separator_to_use)
                    good_splits = merged_text

                # Recursively split the large split
                if separator == "":
                    # Can't split further
                    good_splits.append(s)
                else:
                    # Try the next separator
                    other_info = self._split_text(
                        s, separators[separators.index(separator) + 1 :]
                    )
                    good_splits.extend(other_info)

        # Final merge of remaining good splits
        if good_splits:
            merged_text = self._merge_splits(good_splits, separator_to_use)
            return merged_text

        return []

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """
        Merge splits while respecting chunk_size and chunk_overlap.

        Args:
            splits: List of text splits to merge
            separator: The separator used between splits

        Returns:
            A list of merged chunks
        """
        separator_len = len(separator)
        good_splits = []
        current_merge = []
        total_len = 0

        for s in splits:
            s_len = len(s)

            if (
                total_len + s_len + (separator_len if current_merge else 0)
                <= self.chunk_size
            ):
                # This split fits in the current chunk
                current_merge.append(s)
                total_len += s_len + (separator_len if len(current_merge) > 1 else 0)
            else:
                # Current chunk is full, save it and start a new one
                if current_merge:
                    merged = separator.join(current_merge)
                    good_splits.append(merged)

                    # Handle overlap: keep the last part of the current chunk
                    # for the next chunk if overlap is specified
                    if self.chunk_overlap > 0:
                        # Find how much of the last split to keep for overlap
                        overlap_text = separator.join(current_merge)
                        if len(overlap_text) > self.chunk_overlap:
                            overlap_text = overlap_text[-self.chunk_overlap :]
                            current_merge = [overlap_text]
                            total_len = len(overlap_text)
                        else:
                            current_merge = []
                            total_len = 0
                    else:
                        current_merge = []
                        total_len = 0

                # Add the current split to the new chunk
                # Check if adding this split would exceed chunk_size
                if (
                    total_len + s_len + (separator_len if current_merge else 0)
                    <= self.chunk_size
                ):
                    current_merge.append(s)
                    total_len += s_len + (
                        separator_len if len(current_merge) > 1 else 0
                    )
                else:
                    # Even with overlap, this split doesn't fit
                    # Start a fresh chunk with just this split
                    current_merge = [s]
                    total_len = s_len

        # Don't forget the last chunk
        if current_merge:
            merged = separator.join(current_merge)
            good_splits.append(merged)

        return good_splits
