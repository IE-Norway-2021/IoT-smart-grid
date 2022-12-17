import pandas as pd
#import xgboost
#from sklearn.metrics import mean_squared_error
from datetime import datetime, timedelta
from mqtt_payload_decoder import PayloadDecoder


# EXOSCALE_CONFIG_FILE=./config_ro.toml python main.py


'''
Ajout de 5 valeurs anterieur
Et de 1 valeur posterieur : label de prediction
'''
def prepare_feat(df):
    feature = ['p_l1', 'p_l2', 'p_l3']
    label = 'p+1'
    nb_hist = 6
    for i in range(1,nb_hist):
        df = df.join(df.shift(periods=i)['p_l1'].to_frame(f'p_l1-{i}'))
        df = df.join(df.shift(periods=i)['p_l2'].to_frame(f'p_l2-{i}'))
        df = df.join(df.shift(periods=i)['p_l3'].to_frame(f'p_l3-{i}'))
        feature.extend((f'p_l1-{i}',f'p_l2-{i}',f'p_l3-{i}'))
    df = df.join(df.shift(periods=-1)['p'].to_frame(f'p+1'))
    df = df.dropna()
    return df, df[feature], df[label]


def algo(df):
    df, x, y = prepare_feat(df)
    reg = xgboost.XGBRegressor(n_estimators=250, learning_rate=0.01)
    reg.fit(x,y)
    reg.save_model("model_xgboost.json")
    return reg


def predict(df, reg = None):
    if not reg:
        reg = xgboost.XGBRegressor()
        reg.load_model("model_xgboost.json")

    df, x, y = prepare_feat(df)
    predictions = reg.predict(x)

    # plt.plot(df.index, predictions, label='pred')
    # plt.plot(df.index, y, label='test')
    # plt.legend()

    # mse = mean_squared_error(y, predictions, squared=True)
    # print(f'mse = {mse}')

    return predictions


'''
p_l1 : puissance active de la phase 1
q_l2 : puissance reactive de la phase 2
s_l3 : puissance apparente de la phase 3
v    : tension
i    : courant
pf   : facteur de puissance
phi  : angle de déphasage

Toute les valeurs se trouvent dans le fichier "mqtt_msg_format.json"
'''

# prediction somme des trois puissances
# prediction toutes les 10s


def load_data(date_string, nb_days=1):
    # exo = exoscale.Exoscale()
    # bucket = exo.storage.get_bucket("data-smart-grid")
    b_list = []
    sd = datetime.strptime(date_string, '%Y-%m-%d')
    try:
        for _ in range(nb_days):
            str_sd = sd.strftime("%Y-%m-%d")
            b_list.append(bucket.list_files(prefix=f"SE05000160/{str_sd}"))
            sd += timedelta(days=1)
    except:
        return f'error in date or device name'
    
    p_l1 = []
    p_l2 = []
    p_l3 = []
    p_l123 = []
    index = []
    try:
        for bl in b_list:
            for f_buck in bl:
                f = f_buck.content
                while True:
                    binary = f.read(1)
                    try:
                        test = binary[0]
                    except:
                        #print('end of file')
                        break
                    err, data = PayloadDecoder().decode_msg_type(binary)
                    if not err:
                        binary += f.read(data-1)
                        err, data = PayloadDecoder().decode_feature(binary)
                        if not err:
                            #if data['feature_type'] == 17:   # one minute
                            if data['feature_type'] == 16:   # ten seconds
                                p_l1.append(data['p_l1'])
                                p_l2.append(data['p_l2'])
                                p_l3.append(data['p_l3'])
                                p_l123.append(data['p_l1'] + data['p_l2'] + data['p_l3'])
                                index.append(data['timestamp'])
    except Exception as e: 
        return f'error while reading data : {e}'

    idx = pd.to_datetime(index, unit="s")
    df1 = pd.DataFrame(index=idx)
    df1['p_l1'] = p_l1
    df1['p_l2'] = p_l2
    df1['p_l3'] = p_l3
    df1['p'] = p_l123
    return df1


# if __name__ == "__main__":

#     # entrainement avec les données de 2 semaines depuis le 2022-09-19 :
#     print('load training data ...')
#     #df = load_data('2022-09-19',2*7)
#     print('training')
#     #algo(df)

#     # test sur une journée
#     print('load testing data ...')
#     df = load_data('2022-10-17',1)
#     print('predict')
#     predict(df)

#     plt.show()

'''
données disponible <date, nombre d'heure par date (si < 24)>
2022-06-23, 9
2022-06-24 -> 2022-06-28 
2022-06-29, 20
2022-06-30 -> 2022-10-18
2022-10-19, 8
2022-10-20, 10
2022-10-21, 18
2022-10-22 -> 2022-10-25
2022-10-26, 21
'''

'''
exoscale token :
EXOae4cdf4346305e62a4314166
op1N0Q2IVYhGybAMfEnvYIcHul64foS9ybkIM-Qz9f0
'''
