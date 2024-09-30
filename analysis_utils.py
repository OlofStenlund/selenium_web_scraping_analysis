import pandas as pd
import re

# def find_old_qual_ids(search_term: str) -> list:
#     """
#     Returns a list with the IDs in the requested table.
#     searh_term: str, the title to look for.
#     """
#     try:
#         old_qual_df = pd.read_csv(f"qualifications_dfs/{search_term}_qualifications.csv")
#         old_ids = list(old_qual_df["ID"])
#     except:
#         old_ids = []
    
#     return old_ids



def find_qualifications(
        job_title: str, 
        qualifications_list: list[str],
        ids: list,
        jobs_dataframe: pd.DataFrame
    ) -> tuple[pd.DataFrame | list]:
    """
    Scans each add text for the specific words/terms in qualifications_list, and creates DF-rows to be appended to the qualifications DF.
    """
    if len(ids) == 0:
        pass
    else:
        quals = [i.lower() for i in qualifications_list]
        dict_list = []

        for id in ids:
            add = jobs_dataframe.loc[jobs_dataframe["ID"] == id, "addtext"].values[0].lower()
            add = add.replace(",", " ")
            add = add.replace(".", " ")

            job_qual_dict = {"ID": id, "search_term": job_title}
            for ind, val in enumerate(quals):
                pattern = r'\b' + re.escape(val) + r'\b'
                if re.search(pattern, add):
                    job_qual_dict[qualifications_list[ind]] = 1
                elif not re.search(pattern, add):
                    job_qual_dict[qualifications_list[ind]] = 0
            dict_list.append(job_qual_dict)

        qual_df = pd.DataFrame(dict_list)
        return qual_df, ids