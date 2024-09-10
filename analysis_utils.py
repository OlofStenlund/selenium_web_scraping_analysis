import pandas as pd
import re

def find_old_qual_ids(search_term) -> list:
    try:
        old_qual_df = pd.read_csv(f"qualifications_dfs/{search_term}_qualifications.csv")
        old_ids = list(old_qual_df["ID"])
    except:
        old_ids = []
    
    return old_ids



def find_qualifications(search_term, qualifications_list) -> tuple[pd.DataFrame | list]:

    old_ids = find_old_qual_ids(search_term = search_term)
    quals = [i.lower() for i in qualifications_list]
    jobs_dataframe = pd.read_csv(f"{search_term}_continuous_data.csv")
    new_ids = list(jobs_dataframe["ID"])
    ids = [i for i in new_ids if i not in old_ids]
    dict_list = []

    for id in ids:
        add = jobs_dataframe.loc[jobs_dataframe["ID"] == id, "addtext"].values[0].lower()
        add = add.replace(",", " ")
        add = add.replace(".", " ")

        job_qual_dict = {"ID": id, "search_term": search_term}
        for ind, val in enumerate(quals):
            pattern = r'\b' + re.escape(val) + r'\b'
            if re.search(pattern, add):
                job_qual_dict[qualifications_list[ind]] = 1
            elif not re.search(pattern, add):
                job_qual_dict[qualifications_list[ind]] = 0
        dict_list.append(job_qual_dict)

    qual_df = pd.DataFrame(dict_list)
    return qual_df, ids