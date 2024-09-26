import h5py
import os 
import pandas as pd 

# Definimos función construye rutas
build_path = lambda rutas : os.path.abspath(os.path.join(*rutas))

# Definimos rutas
PATH_FILE = os.getcwd()
DATA_PATH = build_path([PATH_FILE, "..", "datos"])
OUTPUT_PATH = build_path([PATH_FILE, "..", "output"])

FILE_EMPLEO_SLV = build_path([DATA_PATH, "matrices_laborales_slv.h5"])
FILE_CW_CEPAL = build_path([DATA_PATH, "correspondencia_sa_iot_lac.csv"])
FILE_CW_ISIC = build_path([DATA_PATH, "cw_isic_rev_3_to_isic_rev_4.csv"])

# Carga datos de empleo
empleo_slv = h5py.File(FILE_EMPLEO_SLV, "r")

empleo_slv_2014 = empleo_slv["SLV"]["datos"]["ciiu-original"]["2013-2022"][1]
tags = [str(i, encoding = "UTF-8")  for i in empleo_slv["SLV"]["tags"]["ciiu-original"][:]]

df_empleo_slv = pd.DataFrame({i:[j] for i,j in zip(tags[1:], empleo_slv_2014[1:])})

# Carga cw cepal
cw_cepal = pd.read_csv(FILE_CW_CEPAL)

# Carga cw isic
cw_isic = pd.read_csv(FILE_CW_ISIC)
cw_isic["isic_rev_3"] = cw_isic["isic_rev_3"].apply(lambda x : f"{x:04}")
cw_isic["isic_rev_4"] = cw_isic["isic_rev_4"].apply(lambda x : f"{x:04}")

# Función que hace el cw isic 3 - isic 4
def calcula_cw(actividades : str, cw_isic : pd.DataFrame)-> str:
    return ",".join(cw_isic[cw_isic["isic_rev_3"].isin(actividades.split(","))]["isic_rev_4"].unique())


cw_cepal["isic_code_rev_4"] = cw_cepal.isic_code_rev_3.apply(lambda x : calcula_cw(x, cw_isic))


### Calculamos empleo para cada categoría
def calcula_empleo(actividades : str, 
                   datos_empleo : pd.DataFrame) -> int:

    actividades_match = list(
        set(actividades.split(",")).intersection(datos_empleo.columns)
    ) 

    if actividades_match:
        return datos_empleo[actividades_match].sum(axis = 1)[0]
    else:
        return 0


cw_cepal["empleo"] = [calcula_empleo(i, df_empleo_slv) for i in cw_cepal["isic_code_rev_4"]]
cw_cepal = cw_cepal.drop(columns = ["isic_code_rev_3", "isic_code_rev_4"])

## Guardamos los resultados
EMPLEO_CEPAL_FILE_PATH = build_path([OUTPUT_PATH, "cepal_cat_empleo_slv_2014.csv"])

cw_cepal.to_csv(EMPLEO_CEPAL_FILE_PATH, index = False)