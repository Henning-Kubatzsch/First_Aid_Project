# src/rag/chunk.py
from __future__ import annotations
import re
import hashlib
from typing import List, Dict, Any, Optional
from rag.interfaces import Chunker


class CustomChunker(Chunker):
    """
    Get generated text file with following format:

    ---
    Question:
    * question 1
    * question 2
    * question 3

    Title:
    * task 1
    * task 2
    * task 3
    ---

    ...then create create dict and embed each question individually. Then add tasks as context 
    to each question and append to chunks

    """
    def __init__(self):
        pass

    # =========================
    # second approach
    # =========================

    def _clean_and_split_text(self, text: str) -> List[str]:
        text = re.sub(r'[\*+]' , '', text)
        sections = re.split(r'---', text)
        return sections
    
    def _create_section_lists(self, sections: List[str]) -> List[List[str]]:
        section_lists = []
        for i, item in enumerate(sections):
            list_section = re.split(r'\n{1,}', item)
            filtered = [x.strip() for x in list_section if x.strip()]
            if filtered:
                section_lists.append(filtered)
        return section_lists
    
    def _create_section_dictionary(self, section_list : List[List[str]]) -> Dict[int, Dict[str, Any]]:
        sections_dict = {}
        for i, item1 in enumerate(section_list):
            questions = []
            tasks = []
            length = len(section_list)
            section_headers = []
            for j, item2 in enumerate(section_list[i]):
                if re.findall(r'\:\Z', item2):
                    section_headers.append(j)
            sections_dict[i] = {
                'questions' : item1[1:section_headers[1]],
                'tasks' : item1[(section_headers[1]+1):]
            }
        return sections_dict  

    def _create_iterable_chunks(self, sections_dict : Dict[int, Dict[str, Any]], meta: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        meta = meta or {}
        chunks = []
        for i in range(len(sections_dict)):
            for j, item in enumerate(sections_dict[i]['questions']):
                cid = hashlib.sha1(item.encode("utf-8")).hexdigest()[:16]
                out = {"id" : cid, "question": item, "text" : sections_dict[i]["tasks"], "meta" : dict(meta)}
                chunks.append(out)
        return chunks
                    

    # =====================
    # wiring
    # =====================

    def split(self, text: str, meta: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:

        print("we are in custom chunker")
        meta = meta or {}
  
        sections = self._clean_and_split_text(text)
        splitted_sections = self._create_section_lists(sections)
        sections_dict = self._create_section_dictionary(splitted_sections)
        iterable_chunks = self._create_iterable_chunks(sections_dict, meta) 
        
        return iterable_chunks
