import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import Lasso
import os
from glob import glob
from pprint import pprint
from sklearn.preprocessing import StandardScaler
from scipy import signal
from datetime import datetime
import cv2

class SPM2Open_npz():  # second_spm.pyとして実装済み
    def unpack(self, files):
#         print("===== npzファイルの解体 =====")
        print("読み込むフレーム数 : ", len(files))
        data_list_all_time = []
        label_list_all_time = []
        for file in files:
            data_per_pic, label_list_per_pic = self.load(file)
            data_list_all_time.append(data_per_pic)
            label_list_all_time.append(label_list_per_pic)
        data_list_all_time = np.array(data_list_all_time)
        label_list_all_time = np.array(label_list_all_time,dtype=object)

#         print("===== windowごとに集計 =====")
#         print("window数 : 6 (固定中。変更の場合はコード編集が必要）")
        self.data_list_all_win = [[], [], [], [], [], []]
        self.label_list_all_win = [[], [], [], [], [], []]
        for pic, lab_pic in zip(data_list_all_time, label_list_all_time):
            for win_no, (win, label_win) in enumerate(zip(pic, lab_pic)):
                win = np.array(win)
                label_win = np.array(label_win)
                self.data_list_all_win[win_no].append(win.flatten())
                self.label_list_all_win[win_no].append(label_win.flatten())
                # print(train_X.shape)
                pass

        self.data_list_all_win = np.array(self.data_list_all_win,dtype=object)
        self.label_list_all_win = np.array(self.label_list_all_win,dtype=object)

#         print(f"画像加工の種類 : {win.shape[0]}種類")
#         print(f"ヒストグラム特徴量の種類 : {win.shape[1]}種類")
#         print(f"--- >>  合計 : {win.flatten().shape[0]}種類")
#         print("===== 終了 =====")

        return self.data_list_all_win, self.label_list_all_win

    def load(self, file):
        pic = np.load(file, allow_pickle=True)['array_1'][0]
        feature_keys = list(pic.keys())
        list_master = [[], [], [], [], [], []]
        list_master_label = [[], [], [], [], [], []]
        for f_key in feature_keys:
            window_keys = list(pic[f_key].keys())
            for i, w_key in enumerate(window_keys):
                # print(list(pic[f_key][w_key].values()))
                list_master[i].append(list(pic[f_key][w_key].values()))
                labels=[]
                for feature in list(pic[f_key][w_key].keys()):
                    labels.append(f"{w_key}-{f_key}-{feature}")
                        #labels.append(f"{f_key}")
                list_master_label[i].append(labels)
        list_master = np.array(list_master,dtype=object)
        return list_master, list_master_label


"""
    # 削除予定 (__init__を廃止したため、returnが可能になった)
    def get_data(self):
        return self.data_list_all_win,self.label_list_all_win
"""


class SPM2Learn():  # second_spm.pyとして実装済み
    """
    dataからmodelを作る。
    """

    def start(self, data_list_all_win, label_list_all_win, f1, f2, alpha=1.0, f1f2_array_window_custom=None) -> None:
        self.data_list_all_win = data_list_all_win
        self.label_list_all_win = label_list_all_win
        self.alpha = alpha
        # print(data_list_all_win.shape)#(win,pic_num,feature)=(6,886,30)
        if f1f2_array_window_custom == None:
            self.f1 = f1
            self.f2 = f2
            self.f1f2_array_window_custom = np.zeros((self.data_list_all_win.shape[0], 2))
            self.f1f2_array_window_custom[:, 0] = int(self.f1)
            self.f1f2_array_window_custom[:, 1] = int(self.f2)
            # pprint(self.f1f2_array_window_custom)
        else:
            self.f1f2_array_window_custom = f1f2_array_window_custom
            pass
        self.initialize_model()
        self.fit()
        return self.model_master, self.label_list_all_win, self.scaler_master

    def initialize_model(self):
        self.model_master = []
        self.standardization_master = []
        self.scaler_master = []
        for i in range(self.data_list_all_win.shape[0]):
            self.model_master.append(Lasso(alpha=self.alpha,max_iter=100000))
            self.standardization_master.append(StandardScaler())
            self.scaler_master.append("")

    def fit(self):
        SPMSECOND_MIN = -100
        SPMSECOND_MAX = 100
        try:
            train_X2=self.data_list_all_win[0]
            train_X_memorization=self.data_list_all_win[0]
            train_y2=np.full((train_X_memorization.shape[0],1),SPMSECOND_MIN)
            train_y2[-int(self.f1f2_array_window_custom[0][1]):int(
                    -self.f1f2_array_window_custom[0][0])] = SPMSECOND_MAX
            self.scaler_master[0] = self.standardization_master[0].fit(train_X2)

            for win_no, win in enumerate(self.data_list_all_win[1:]):
                win_no+=1
                train_X2=np.vstack([train_X2,win])
                self.scaler_master[win_no] = self.standardization_master[win_no].fit(train_X2)
                train_X = self.scaler_master[win_no].transform(train_X2)
                train_y2_win = np.full((train_X_memorization.shape[0], 1), SPMSECOND_MIN)
                train_y2_win[-int(self.f1f2_array_window_custom[win_no][1]):int(
                    -self.f1f2_array_window_custom[win_no][0])] = SPMSECOND_MAX
                train_y2=np.vstack([train_y2,train_y2_win])
                print(train_y2.shape)

    #             train_X=train_X2
            print("SPM2 will be excetuted by integrated model across all windows")
            train_X=train_X
            train_y=train_y2
            for win_no, win in enumerate(self.data_list_all_win):
                self.model_master[win_no].fit(train_X, train_y)
            
        except Exception as e:
            print(e)
            print("SPM2 will be excecuted by each model for each window")
            for win_no, win in enumerate(self.data_list_all_win):
                train_X = win
                self.scaler_master[win_no] = self.standardization_master[win_no].fit(train_X)
                train_X = self.scaler_master[win_no].transform(train_X)
                train_y = np.full((train_X.shape[0], 1), SPMSECOND_MIN)
                # print(self.f1f2_array_window_custom[win_no][0])
                train_y[-int(self.f1f2_array_window_custom[win_no][1]):int(
                    -self.f1f2_array_window_custom[win_no][0])] = SPMSECOND_MAX
                # print(train_X.shape, train_y.shape)
                self.model_master[win_no].fit(train_X, train_y)


    def get_nonzero_w(self):
        self.nonzero_w = []
        self.nonzero_w_label = []
        for win_no, (win_model, labels) in enumerate(zip(self.model_master, self.label_list_all_win)):
            self.nonzero_w.append([])
            self.nonzero_w_label.append([])
            weight = win_model.coef_
            labels = labels[0]
            for (w, label) in zip(weight, labels):
                if abs(w) > 1:
                    self.nonzero_w[win_no].append(w)
                    self.nonzero_w_label[win_no].append(label)
              
        self.nonzero_w_num = np.array([
            [len(self.nonzero_w_label[0]), len(self.nonzero_w_label[1]), len(self.nonzero_w_label[2])],
            [len(self.nonzero_w_label[3]), len(self.nonzero_w_label[4]), len(self.nonzero_w_label[5])]
        ])
        return self.nonzero_w, self.nonzero_w_label, self.nonzero_w_num

  
    def get_data(self):
        return self.model_master,self.label_list_all_win,self.scaler_master



class SPM2Evaluate():  # 藤井さんの行動計画側に移設予定
    def start(self, model_master, test_data_list_all_win, test_label_list_all_win, scaler_master,score_master_mother):
        self.model_master = model_master
        self.test_data_list_all_win = test_data_list_all_win
        self.test_label_list_all_win = test_label_list_all_win
        self.scaler_master = scaler_master
        self.score_master_mother=score_master_mother
        if len(self.model_master) != len(self.test_data_list_all_win):
            print("学習済みモデルのウィンドウ数と、テストデータのウィンドウ数が一致しません")
            return None
        self.test()
        return self.score_master

    def test(self):
        self.score_master = []
        for win_no in range(np.array(self.test_data_list_all_win).shape[0]):
            self.score_master.append([])
        for test_no in range(np.array(self.test_data_list_all_win).shape[1]):
            for win_no, win in enumerate(self.test_data_list_all_win):
                test_X = win[test_no]
                test_X = self.scaler_master[win_no].transform(
                    test_X.reshape(1, -1))
                score = self.model_master[win_no].predict(
                    test_X.reshape(1, -1))
                self.score_master[win_no].append(score)
                weight = self.model_master[win_no].coef_
        #self.apply_moving_average()

    def apply_moving_average(self):
        if self.score_master_mother==[]:
            pass
        else:        
            self.score_master_np=np.array(self.score_master)    
            self.score_master_mother.append(self.score_master_np)
            self.score_master_mother=np.array(self.score_master_mother)
            self.score_master=self.score_master_mother.mean(axis=0)
            self.score_master=self.score_master.tolist()
     
    def get_score(self):
        return self.score_master
        # pprint(self.score_master[0])


    def plot(self, save_dir):
        for i, win_score in enumerate(self.score_master):
            win_score = np.array(win_score).flatten()
            win_score_mov_ave = self.moving_average(win_score)
            win_score_low = self.lowpass(win_score, 25600, 100, 600, 3, 40)
            plt.plot(np.arange(len(win_score_mov_ave)),win_score_mov_ave, label=f"win_{i+1}", color="r")
            plt.plot(np.arange(len(win_score)),win_score_low, label=f"win_{i+1}")
        plt.xlabel("time")
        plt.ylabel("degree of risk")
        plt.ylim((-200, 200))
        global train_mov_code, test_mov_code, alpha
        plt.title(f"{train_mov_code} -->> {test_mov_code}  alpha={alpha}")
        plt.legend()
        name = str(datetime.now()).replace(" ", "").replace(":", "").replace("-", "").replace(".", "")[:16]
        plt.savefig(save_dir+f"/cca{train_mov_code}{test_mov_code}_{name}.jpg")
        plt.cla()

        # plt.show()

    def moving_average(self, x, num=50):
        ave_data = np.convolve(x, np.ones(num)/num, mode="valid")
        return ave_data

    def lowpass(self, x, samplerate, fp, fs, gpass, gstop):
        fn = samplerate / 2  # ナイキスト周波数
        wp = fp / fn  # ナイキスト周波数で通過域端周波数を正規化
        ws = fs / fn  # ナイキスト周波数で阻止域端周波数を正規化
        N, Wn = signal.buttord(wp, ws, gpass, gstop)  # オーダーとバターワースの正規化周波数を計算
        b, a = signal.butter(N, Wn, "low")  # フィルタ伝達関数の分子と分母を計算
        y = signal.filtfilt(b, a, x)  # 信号に対してフィルタをかける
        return y

    def get_nonzero_w(self):
        self.nonzero_w = []
        self.nonzero_w_label = []
        for win_no, (win_model, labels) in enumerate(zip(self.model_master, self.test_label_list_all_win)):
            self.nonzero_w.append([])
            self.nonzero_w_label.append([])
            weight = win_model.coef_
            labels = labels[0]
            for (w, label) in zip(weight, labels):
                if w > 1:
#                     print("weight: \n", weight.shape)
#                     print("labels: \n", labels.shape)
                    self.nonzero_w[win_no].append(w)
                    self.nonzero_w_label[win_no].append(label)
        self.nonzero_w_num = np.array([
            [len(self.nonzero_w_label[0]), len(self.nonzero_w_label[1]), len(self.nonzero_w_label[2])],
            [len(self.nonzero_w_label[3]), len(self.nonzero_w_label[4]), len(self.nonzero_w_label[5])]
        ])
        return self.nonzero_w, self.nonzero_w_label, self.nonzero_w_num


    def special_plot(self, save_dir):
        for i, win_score in enumerate(self.score_master):
            win_score = np.array(win_score).flatten()
            win_score_mov_ave = self.moving_average(win_score)
            # win_score_low = self.lowpass(win_score, 25600, 100, 600, 3, 40)
            # plt.plot(np.arange(len(win_score)),win_score, label=f"win_{i+1}")
            plt.plot(np.arange(len(win_score_mov_ave)),win_score_mov_ave, label=f"win_{i+1}_ave")
            # plt.plot(np.arange(len(win_score)),win_score_low, label=f"win_{i+1}_lpf")
        plt.xlabel("time")
        plt.ylabel("degree of risk")
        plt.ylim((-200, 200))
        plt.title(f"test_results")
        plt.legend()
        name = str(datetime.now()).replace(" ", "").replace(":", "").replace("-", "").replace(".", "")[:16]
        plt.savefig(save_dir+f"{name}.jpg")
        plt.cla()

    def analysis_movie(self,save_dir):
        hist=[[],[],[],[],[],[]]
        hist_th=[[],[],[],[],[],[]]

        index=[]
        imgs=sorted(glob("/home/ytpc2019a/code_ws/temp/cansat/images/*"))
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        video = cv2.VideoWriter(save_dir+'th100.mp4',fourcc, 20, (1500, 1000))
        for i, (img_path,w1,w2,w3,w4,w5,w6) in enumerate(zip(imgs,self.score_master[0],self.score_master[1],self.score_master[2],self.score_master[3],self.score_master[4],self.score_master[5])):
            for j, w in enumerate([w1,w2,w3,w4,w5,w6]):
                hist[j].append(w)
                if w>=100:
                    w=[10]
                elif w<-100:
                    w=[-10]
                else:
                    pass
                hist_th[j].append(w)
            index.append(i)
            plt.subplots(figsize=(15.0, 10.0))
            plt.subplot(5, 1, 1,)
            img=cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            plt.imshow(img)
            plt.subplot(5,1,2)
            plt.title("raw data")
            for j in range (6):
                plt.plot(index,hist[j],label=f"w_{j+1}")
            plt.legend(loc='lower left')
            plt.subplot(5,1,3)
            plt.title("cut |danger|>10")
            for h in range (6):
                plt.plot(index,hist_th[h],label=f"w_{h+1}")
            plt.legend(loc='lower left')
            plt.subplot(5,1,4)
            plt.title("moving average 3")
            for h in range (6):
                # try:
                no=3
                if len(hist_th[h])<no:
                    no=len(hist_th[h])
                print("no",no)
                print(index,np.array(hist_th[h]).flatten())
                # print(self.moving_average(np.array(hist_th[h]).flatten()[:-no+1],num=no))
                if no<2:
                    plt.plot(index,hist_th[h],label=f"w_{h+1}")
                else:
                    plt.plot(index,self.moving_average(np.array(hist_th[h]).flatten()[:-no+1],num=no),label=f"w_{h+1}")
            # plt.legend(loc='lower left')
            plt.subplot(5,1,5)
            plt.title("moving average 5")
            for h in range (6):
                # try:
                no=5
                if len(hist_th[h])<no:
                    no=len(hist_th[h])
                print("no",no)
                print(index,np.array(hist_th[h]).flatten())
                # print(self.moving_average(np.array(hist_th[h]).flatten()[:-no+1],num=no))
                if no<2:
                    plt.plot(index,hist_th[h],label=f"w_{h+1}")
                else:
                    plt.plot(index,self.moving_average(np.array(hist_th[h]).flatten()[:-no+1],num=no),label=f"w_{h+1}")


            
            # plt.subplot(2,3,4)
            # plt.bar(np.array([1,2,3]), np.array([w1[0],w2[0],w3[0]]))
            # plt.subplot(2,3,5)
            # plt.bar(np.array([4,5,6]), np.array([w4[0],w5[0],w6[0]]))
            plt.savefig(save_dir+"test.jpg")
            plt.clf()
            img2=cv2.imread(save_dir+"test.jpg")
            video.write(img2)
        video.release()

alpha=5.0



additional_pic_npz_dir="/Users/hayashidekazuyuki/Desktop/Git_Win_Air/wolvez_database/pre_data"
exp1_npz_dir="/Users/hayashidekazuyuki/Desktop/Git_Win_Air/wolvez_database/planning_npz_exp1"

learn_npz_paths=sorted(glob(additional_pic_npz_dir+"/*"))
test_npz_paths=sorted(glob(exp1_npz_dir+"/*"))

learn_open_npz=SPM2Open_npz()
data_list_all_win,label_list_all_win = learn_open_npz.unpack(learn_npz_paths)

spm2_learn=SPM2Learn()

model_master,label_list_all_win,scaler_master=spm2_learn.start(data_list_all_win,label_list_all_win,1,50,alpha=alpha)
nonzero_w, nonzero_w_label, nonzero_w_num=spm2_learn.get_nonzero_w()
pprint(nonzero_w_label)
print(np.array(nonzero_w_label).shape)
test_open_npz=SPM2Open_npz()

score_master_mother=[]
spm2_test=SPM2Evaluate()
for i, test_npz_path in enumerate(test_npz_paths):
    test_data_list_all_win,test_label_list_all_win = test_open_npz.unpack([test_npz_path])
    score_master=spm2_test.start(model_master,test_data_list_all_win,test_label_list_all_win,scaler_master,score_master_mother)
    print(i,np.array(score_master).reshape(1,-1))
    score_master_mother.append(score_master)
plt.hist(np.array(score_master_mother).reshape(-1,),bins=100,log=True)
plt.title(f"alpha={alpha},label=100")
plt.show()



"""
・帰り際に撮った200+50枚を学習
・投下走行の時の画像を推論
・妥当なalphaを調節で決める
"""
