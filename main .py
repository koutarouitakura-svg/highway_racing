import pyxel
import math
import random
import json
import os
class App:
    GEAR_SETTINGS = [
                {"accel": 1.0,  "max_vel": 0.15},
                {"accel": 0.7,  "max_vel": 0.30},
                {"accel": 0.5,  "max_vel": 0.45},
                {"accel": 0.35, "max_vel": 0.55},
                {"accel": 0.30,  "max_vel": 0.70},
            ]
    def __init__(self):
        self.save_file = "best_times.json"
        # シーン管理用の定数
        self.STATE_TITLE = 0 #タイトル
        self.STATE_MENU = 1 #メニュー
        self.STATE_PLAY = 2 #プレイ開始
        self.STATE_PAUSE = 3 # ポーズ状態を追加
        self.STATE_CUSTOMIZE = 4 # カスタマイズ状態
        self.state = self.STATE_TITLE 
        self.is_night_mode = False
        self.is_automatic = False # オートマフラグ
        self.goal_distance = 5.0
        # Pyxelの初期化
        pyxel.init(200, 150, title="Highway Racer", quit_key=pyxel.KEY_NONE)
        # サウンドの初期設定
        self.setup_sounds()
        # エンジン音再生用の変数
        self.engine_sound_enabled = True
        # パレットと画像のロード
        self.setup_custom_palette()
        pyxel.images[0].load(0, 0, "car.png")
        pyxel.images[1].load(0, 0, "cloud.png")
        pyxel.images[2].load(0, 0, "title.png")
        self.car_color = 195
        self.reset()
        self.best_times = self.load_best_times()
        pyxel.run(self.update, self.draw)

    def setup_sounds(self):
        # 0: エンジン音 (ループ用)
        pyxel.sounds[0].set("c1a0 ", "n", "6", "n", 2)
        pyxel.sounds[0].volumes[0] = 4
        # 1: クリック音 (カチッ)
        pyxel.sounds[1].set("c3", "p", "2", "n", 5)
        # 2: 場面転換音 (フォン)
        pyxel.sounds[2].set("c2e2g2c3", "s", "6", "f", 10)
        # 3: ファンファーレ (ゴール)
        pyxel.sounds[3].set("c3e3g3b3 c3e3g3b3 d3f#3a3c#4 d3f#3a3c#4 g3r g3r g4", "s", "6", "f", 7)
        # 4: 衝突音 (ドカン)
        pyxel.sounds[4].set("c1c1c1", "n", "7", "f", 20)
        # 5: ニトロ（シュゴーー）
        pyxel.sounds[5].set("c4d4e4g4","s","5","v",5)

    def load_best_times(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r") as f:
                    data = json.load(f)
                    # 重要：JSONのキーは必ず文字列なので、数値(float)に変換して復元する
                    return {float(k): v for k, v in data.items()}
            except Exception as e:
                print(f"Load Error: {e}")
        # ファイルがない、または読み込めない場合のデフォルト
        return {1.0: None, 3.0: None, 5.0: None, 10.0: None}

    def save_best_times(self):
        try:
            with open(self.save_file, "w") as f:
                # 数値をキーにした辞書を保存
                json.dump(self.best_times, f)
        except Exception as e:
            print(f"Save Error: {e}")

    def reset(self):
        self.setup_sounds()
        self.is_respawning = False
        self.respawn_timer = 0
        self.gear = 0
        self.rpm = 0
        self.display_rpm = 0  # 追加：メーター表示用のRPM
        self.speed = 0
        self.car_x = 0
        self.velocity = 0
        self.kilometer = 0
        self.u = 49
        self.w = 50 
        self.total_distance = 0.0
        self.odometer = 0.0
        self.is_goal = False
        self.is_braking = False
        self.is_kanban = False
        self.is_out = False
        self.is_new_record = False
        self.out_darkness = 0  # コースアウト時の暗さを管理 (0〜100)
        self.car_draw_y = 95
        self.frame_count = 0
        self.goal_time = 0
        self.wind_particles = []
        self.confetti = [] # 紙吹雪用
        self.is_boosting = False      # ブースト中かどうかのフラグ
        self.boost_timer = 0          # ブーストの残り時間
        self.boost_cooldown = 0       # 次にブーストできるまでの待ち時間
        self.is_rocket_start = False
        self.rocket_timer = 0
        self.rocket_text_timer = 0
        self.is_stalled = False
        self.stall_timer = 0
        self.track_pos = 0
        self.curve_val = 0
        self.target_curve = 0
        self.road_objects = []
        self.tree_span = 120.0
        self.dbg_x = 135
        self.dbg_y = 5
        self.is_spinning = False  # スピン中フラグ
        self.spin_timer = 0       # スピンの経過時間
        self.shake_amount = 0  # 衝撃による揺れの強さ
        self.grass_shake = 0   # 芝生による現在の揺れ幅
        self.road_objects = []
        for i in range(40):
            obj_type = "tree" if random.random() > 0.2 else "sign"
            side = random.choice([-2.25, 2.25])
            
            if obj_type == "sign":
                # 縁石のすぐ隣（マージン 5〜10）
                margin = random.uniform(5, 10)
            else:
                # 木は少し離れた場所（マージン 20〜50）
                margin = random.uniform(20, 50)
            
            self.road_objects.append({
                "depth": i * 3.0, 
                "margin_x": margin * side, # offset_x から margin_x に名前変更
                "size": random.uniform(1.0, 1.3),
                "type": obj_type,
                "color": random.choice([10, 12, 14])
            })

        # --- 追加：ライバル車（NPC）の設定 ---
        self.is_respawning = False
        self.respawn_timer = 0
        self.rival_cars = []
        self.spawn_queue_timer = 0
        self.start_timer = 200
        self.track_data = []
        for _ in range(50):
            self.track_data.append(random.uniform(-1.5, 1.5))
            
        self.clouds = []
        while len(self.clouds) < 5:
            c_type = random.choice([0, 1])
            cw, ch, u, v = (45, 15, 0, 0) if c_type == 0 else (30, 20, 0, 15)
            self.clouds.append({
                "x": random.uniform(0, pyxel.width),
                "y": random.uniform(5, 40),
                "depth": random.uniform(0.1, 0.8),
                "u": u, "v": v,
                "orig_w": cw, "orig_h": ch,
                "speed_factor": random.uniform(0.05, 0.1)
            })

    def spawn_rival(self, depth):
        # 色のバリエーションを増加 (2:茶, 14:ピンク, 15:肌色, 12:青, 10:黄, 3:緑)
        rival_colors = [2, 14, 15, 12, 10, 3, 9, 11]
        self.rival_cars.append({
            "depth": depth,
            "offset_x": random.uniform(-90, 90),
            "speed_kmh": random.uniform(140, 210), # 速度差を少し縮めて団子状態を防ぐ
            "col": random.choice(rival_colors),
            "is_blown": False,
            "blown_timer": 0
        })


    def setup_custom_palette(self):
        original_palette = pyxel.colors.to_list()
        step_val = 0x33
        new_colors = [
            ((i % 6) * step_val) + 
            (((i // 6) % 6) * step_val) * 0x100 + 
            (((i // 36) % 6) * step_val) * 0x10000 
            for i in range(1, 216)
        ]
        combined_palette = original_palette + new_colors
        pyxel.colors.from_list(combined_palette[:230])
    

    def update(self):
        if self.state == self.STATE_TITLE:
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.state = self.STATE_MENU
                pyxel.play(1, 2) # シーン切り替え音
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                pyxel.quit()

        
        elif self.state == self.STATE_MENU:
            if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_DOWN) or \
               pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_N) or pyxel.btnp(pyxel.KEY_C):
                pyxel.play(1, 1)
            if pyxel.btnp(pyxel.KEY_UP, 10, 2):
                self.goal_distance = round(self.goal_distance + 0.1, 1)
                pyxel.play(1, 1)
            if pyxel.btnp(pyxel.KEY_DOWN, 10, 2):
                self.goal_distance = max(0.1, round(self.goal_distance - 0.1, 1))
                pyxel.play(1, 1)
            if pyxel.btnp(pyxel.KEY_A): # オートマ切替
                self.is_automatic = not self.is_automatic
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.state = self.STATE_PLAY
                pyxel.play(1, 2)
                self.reset()
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                self.state = self.STATE_TITLE
            if pyxel.btnp(pyxel.KEY_N):
                self.is_night_mode = not self.is_night_mode
            if pyxel.btnp(pyxel.KEY_C): self.state = self.STATE_CUSTOMIZE # カスタマイズへ

        elif self.state == self.STATE_PAUSE:
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                self.state = self.STATE_PLAY
            if pyxel.btnp(pyxel.KEY_R):
                self.state = self.STATE_MENU
                self.reset()

        elif self.state == self.STATE_CUSTOMIZE:
            if pyxel.btnp(pyxel.KEY_1): 
                self.car_color = 195  # 赤
                pyxel.play(1, 1)
            if pyxel.btnp(pyxel.KEY_2): 
                self.car_color = 12 # 青
                pyxel.play(1, 1)
            if pyxel.btnp(pyxel.KEY_3): 
                self.car_color = 10 # 黄
                pyxel.play(1, 1)
            if pyxel.btnp(pyxel.KEY_4): 
                self.car_color = 11 # 緑
                pyxel.play(1, 1)
            if pyxel.btnp(pyxel.KEY_5): 
                self.car_color = 14 # 紫
                pyxel.play(1, 1)
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                self.state = self.STATE_MENU
                pyxel.play(1, 1)

        elif self.state == self.STATE_PLAY:
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                self.state = self.STATE_PAUSE
                pyxel.stop(0)
                return


            # --- RPMの基本計算（走行中または空ぶかし） ---
            target_rpm = 0
            if self.start_timer > 0:
                # カウントダウン中：UPキーで空ぶかし
                if pyxel.btn(pyxel.KEY_UP):
                    target_rpm = 0.9 + random.uniform(-0.05, 0.05) # 針を震わせる
                else:
                    target_rpm = 0
            else:
                # 走行中：速度とギアに基づく本来のRPM
                gear_set = self.GEAR_SETTINGS[self.gear]
                target_rpm = self.velocity / gear_set["max_vel"]

            # 表示用RPMをターゲットに近づける（徐々に戻る・動くロジック）
            # 0.2 は追従速度。値を小さくするとよりゆっくり戻ります
            if self.start_timer == 0:
                real_target_rpm = self.velocity / gear_set["max_vel"]
                # display_rpm を走行用RPMに徐々に近づける
                self.display_rpm += (real_target_rpm - self.display_rpm) * 0.1
            self.display_rpm += (target_rpm - self.display_rpm) * 0.2
            self.rpm = self.display_rpm # メーター描画ロジックが参照する変数に代入

            
            if self.STATE_PLAY:
                # RPMに合わせて音程を決定
                note = int(12 + self.display_rpm * 24)
                pyxel.sounds[0].notes[0] = note
                pyxel.sounds[0].notes[1] = note
                pyxel.play(0, 0, loop=True)
            else:
                # 条件外（ゴールや停止中）なら即座に停止
                pyxel.stop(0)
            #オートマチック
            if self.is_automatic and self.start_timer == 0 and not self.is_goal:
                if self.rpm > 0.85 and self.gear < 4:
                    self.gear += 1
                elif self.rpm < 0.6 and self.gear > 0:
                    self.gear -= 1

            for c in self.confetti[:]:
                c["x"] += c["vx"]
                c["y"] += c["vy"]
                c["vy"] += 0.05
                c["angle"] += c["va"]
                if c["y"] > pyxel.height: self.confetti.remove(c)
            if self.start_timer > 0:
                self.start_timer -= 1
                self.velocity = 0
                if self.start_timer > 40 and pyxel.btn(pyxel.KEY_UP):
                    self.is_stalled = True
                elif not pyxel.btn(pyxel.KEY_UP):
                    self.is_stalled = False
                if 10 < self.start_timer < 40 and pyxel.btn(pyxel.KEY_UP):
                    if not self.is_stalled:
                     self.is_rocket_start = True
                elif self.start_timer < 10 and not pyxel.btn(pyxel.KEY_UP):
                    self.is_rocket_start = False # 離しちゃダメ
                if self.start_timer == 0:
                    self.frame_count = 0
                    if self.is_stalled:
                        self.stall_timer = 60 # 2秒間動けない
                        self.velocity = 0
                    elif self.is_rocket_start:
                        self.velocity = 0.25
                        self.rocket_timer = 60
                        self.rocket_text_timer = 60 # テキスト表示用
                    self.rival_cars = [] # 初期化
            else:
                self.frame_count += 1
                if len(self.rival_cars) < 3:
                    if self.spawn_queue_timer > 0:
                        self.spawn_queue_timer -= 1
                    else:
                        self.spawn_rival(800) # 遠く（地平線）にスポーン
                        self.spawn_queue_timer = 90 # 次のスポーンまで約3秒(90フレーム)待つ

            if self.is_respawning:
                self.respawn_timer += 1
                if self.respawn_timer > 30:
                    self.is_respawning = False
                    self.car_x = 0
                return
            #スピン
            if self.is_spinning:
                self.spin_timer += 1
                self.car_x -= self.car_x * 0.1 # 徐々にセンターへ戻る
            
                # スピンのアニメーション（向きを強制的に変える）
                # self.u をタイマーに合わせてループさせることで回転を表現
                spin_frames = [49, -50, 50, -50] # 標準, 左向き, 右向きなどの切り替え
                self.u = spin_frames[(self.spin_timer // 2) % 4]
                self.w = 26 # 旋回用の幅を使用
            
                if self.spin_timer > 30: # 1秒弱で復帰
                    self.is_spinning = False
                    self.is_kanban = False
                    self.spin_timer = 0
                    pyxel.camera(0, 0)
                if not self.is_kanban:
                    return # スピン中は操作不能


            if not self.is_goal and self.start_timer == 0:
                if  self.is_stalled:
                    self.velocity = 0
                    pyxel.play(1,4)
                else:
                    if pyxel.btnp(pyxel.KEY_E): self.gear = min(self.gear + 1, 4)
                    if pyxel.btnp(pyxel.KEY_Q): self.gear = max(self.gear - 1, 0)
                    gear_set = self.GEAR_SETTINGS[self.gear]
                    self.is_braking = False
                    if pyxel.btn(pyxel.KEY_UP):
                        if self.velocity < gear_set["max_vel"]:
                            if not self.is_automatic:
                                self.velocity += 0.002 * gear_set["accel"]  
                            else: 
                                self.velocity += 0.002 * gear_set["accel"] * 0.8
                        else:
                            self.velocity = max(self.velocity - 0.001, gear_set["max_vel"])
                    elif pyxel.btn(pyxel.KEY_DOWN):
                        self.velocity = max(self.velocity - 0.004, 0)
                        self.is_braking = True
                    else:
                        self.velocity = max(self.velocity - 0.0005, 0)
                    if pyxel.btnp(pyxel.KEY_SPACE) and self.boost_cooldown == 0 and not self.is_goal:
                        self.is_boosting = True
                        self.boost_timer = 30  # 2秒間加速（30fps想定なら60フレーム）
                        self.boost_cooldown = 300 # 次に使えるまで10秒間のクールダウン

                    if self.is_boosting:
                        self.velocity = min(self.velocity + 0.005, 0.8) # 通常の最高速(0.7)を超える0.8まで加速
                        self.boost_timer -= 1
                        self.wind_particles.append({
                                "x": pyxel.width / 2 + random.uniform(-10, 10),
                                "y": 110, 
                                "vx": random.uniform(-1, 1),      # 左右の散らばり
                                "vy": random.uniform(2, 5),       # 下方向への勢い
                                "speed_up": 1.1,                  # 加速感
                                "col": random.choice([7, 10])
                        })
                        
                        if pyxel.play_pos(2) is None and self.state != self.STATE_PAUSE:
                            pyxel.play(2, 5, loop=True)
                        else:
                            pyxel.stop(2)
                        if self.boost_timer <= 0:
                            pyxel.stop(2)
                            self.is_boosting = False

                    if self.boost_cooldown > 0:
                        self.boost_cooldown -= 1
            else:
                self.is_braking = False
                if self.start_timer == 0:
                    self.velocity = max(self.velocity - (self.velocity - 0.05)/100, 0.05)
                if abs(self.car_x) > 0.1:
                    self.car_x -= self.car_x * 0.03
                else:
                    self.car_x = 0
                #リスタート
                if pyxel.btnp(pyxel.KEY_R):
                    self.state = self.STATE_MENU
                    pyxel.stop()
                    self.reset()
                    return

            gear_set = self.GEAR_SETTINGS[self.gear]
            self.speed += self.velocity
            self.kilometer = int(self.velocity * 400)


            if not self.is_goal:
                self.total_distance += self.velocity * 0.005
                self.odometer = round(self.total_distance, 2)

            self.track_pos += self.velocity * 5
            current_idx = int(self.track_pos / 150) % len(self.track_data)
            self.target_curve = self.track_data[current_idx]
            self.curve_val += (self.target_curve - self.curve_val) * 0.05

            if not self.is_goal:
                handling_factor = math.sin(max(0, min(self.velocity / 0.6 * math.pi, math.pi)))
                move_amount = 7.5 * handling_factor
                if not self.is_spinning:
                    if pyxel.btn(pyxel.KEY_LEFT): 
                        self.car_x -= move_amount
                        self.u, self.w = -50, 26
                    elif pyxel.btn(pyxel.KEY_RIGHT):
                        self.car_x += move_amount
                        self.u, self.w = 50, 26
                    else:
                        self.u, self.w = 49, 0
                self.car_x -= self.curve_val * (self.velocity * 7)
            else:
                if self.target_curve < -0.5:     # 左カーブ
                    self.u, self.w = -50, 26
                elif self.target_curve > 0.5:    # 右カーブ
                    self.u, self.w = 50, 26
                else:                           # 直進
                    self.u, self.w = 49, 0
            road_limit = 165
            if abs(self.car_x) > road_limit and not self.is_goal:
                self.is_out = True
                self.grass_shake = random.uniform(-2, 2) * self.velocity * 10
                if self.velocity > 0.15:
                    self.velocity = max(self.velocity - 0.005, 0)
                if abs(self.car_x) > 400:
                    self.is_respawning = True
                    self.velocity = 0
                    self.respawn_timer = 0
            else:
                self.is_out = False

            self.vanishing_x = (pyxel.width / 2) + (self.curve_val * 80)
            self.vanishing_y = 60 
            self.update_effects()

            if self.odometer >= self.goal_distance and not self.is_goal:
                pyxel.sounds[0].volumes[0] = 2
                pyxel.play(3, 3) # ファンファーレ
                self.is_goal = True
                self.goal_time = self.frame_count / 30
                dist = float(self.goal_distance) # 確実に型を合わせる
                if dist not in self.best_times or self.best_times[dist] is None or self.goal_time < self.best_times[dist]:
                    self.best_times[dist] = self.goal_time
                    self.save_best_times() # 保存実行
                    self.is_new_record = True
                for _ in range(100):
                        self.confetti.append({
                            "x": random.uniform(0, pyxel.width), "y": random.uniform(-100, 0),
                            "vx": random.uniform(-1, 1), "vy": random.uniform(1, 3),
                            "col": random.choice([7, 8, 9, 10, 11, 12, 14, 15]),
                            "angle": random.uniform(0, 360), "va": random.uniform(5, 15)
                        })
        move_speed = 2
        if pyxel.btn(pyxel.KEY_I): self.dbg_y -= move_speed
        if pyxel.btn(pyxel.KEY_K): self.dbg_y += move_speed
        if pyxel.btn(pyxel.KEY_J): self.dbg_x -= move_speed
        if pyxel.btn(pyxel.KEY_L): self.dbg_x += move_speed
       
        for rival in self.rival_cars:
                rival["offset_x"] += math.sin(pyxel.frame_count * 0.05 + rival["depth"]) * 0.5
                # 1. 吹き飛び中の特殊処理
                if rival.get("is_blown"):
                    pyxel.play(1, 4)
                    rival["blown_timer"] -= 1
                    rival["depth"] += 2.0 
                    if rival["blown_timer"] <= 0:
                        rival["is_blown"] = False
                        rival["speed_kmh"] = random.uniform(120, 180)
                    continue # 吹き飛び中は以下の通常移動をスキップ

                # 2. 【重要】自律走行の計算
                # 自車の速度に関わらず、ライバルは自分の speed_kmh で進み続けます。
                # 描画上の位置(depth)は「ライバルの進んだ距離 - 自車の進んだ距離」で決まります。
                
                rival_vel_factor = rival["speed_kmh"] / 400  # 秒速的な係数に変換
                # 自車が 0 でも rival_vel_factor がプラスなら depth は増え（遠ざかり）ます
                rival["depth"] += (rival_vel_factor - self.velocity) * 100 
                
                # 3. リスポーン判定
                # 後ろに消えた(追い越した)場合、または遠ざかりすぎて見えなくなった場合
                if rival["depth"] < -200 or rival["depth"] > 900:
                    self.rival_cars.remove(rival)
        
    def update_effects(self):
        if self.kilometer > 150:
            spawn_count = int((self.kilometer - 150) / 10)
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(5, 10)
                self.wind_particles.append({
                    "x": self.vanishing_x + math.cos(angle) * dist,
                    "y": self.vanishing_y + math.sin(angle) * dist,
                    "vx": math.cos(angle) * 3,
                    "vy": math.sin(angle) * 3,
                    "speed_up": random.uniform(1.15, 1.3),
                    "col": random.choice([7, 12, 6])
                })
        for p in self.wind_particles[:]:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            p["vx"] *= p["speed_up"]; p["vy"] *= p["speed_up"]
            if p["x"] < -100 or p["x"] > pyxel.width + 100 or p["y"] < -100 or p["y"] > pyxel.height + 100:
                self.wind_particles.remove(p)

        for c in self.clouds:
            c["x"] += self.velocity * c["speed_factor"] * 10
            c["x"] -= self.curve_val * (1.0 - c["depth"]) * self.velocity * 10
            c["x"] += (self.car_x * 0.01) * (1.0 - c["depth"]) * self.velocity * 2
            if c["x"] < -100: c["x"] = pyxel.width + 100
            if c["x"] > pyxel.width + 100: c["x"] = -100

    def draw(self):
        sh_x = random.uniform(-self.shake_amount, self.shake_amount) + self.grass_shake
        sh_y = random.uniform(-self.shake_amount, self.shake_amount)
        
        # 画面全体を揺らす
        pyxel.pal()
        pyxel.cls(0)
        if self.state == self.STATE_TITLE:
            self.draw_title_screen()
        elif self.state == self.STATE_MENU:
            self.draw_menu_screen()
        elif self.state == self.STATE_CUSTOMIZE: 
            self.draw_customize_screen()
        elif self.state == self.STATE_PLAY or self.STATE_PAUSE:
            self.draw_game_scene()
            for c in self.confetti:
                self.draw_confetti(c["x"], c["y"], 3, c["col"], c["angle"])
            if self.is_spinning:
                pyxel.camera(sh_x, sh_y)
            elif self.is_out:
                pyxel.camera(sh_x, sh_y)
            elif self.is_boosting:
                sh_x = random.uniform(-2, 2)
                sh_y = random.uniform(-2, 2)
            else:    
                pyxel.camera(0, 0)
            if not self.is_goal:
                gx, gy = 140, 10  # ゲージの開始位置
                gw, gh = 50, 6    # ゲージのサイズ
                # 外枠
                pyxel.rectb(gx, gy, gw, gh, 7)
                if self.is_boosting:
                    # ブースト中：残り時間に応じてオレンジのゲージが減っていく
                    fill_w = (self.boost_timer / 60) * (gw - 2)
                    pyxel.rect(gx + 1, gy + 1, fill_w, gh - 2, 9) # オレンジ
                    pyxel.text(gx - 25, gy, "NITRO!!", pyxel.frame_count % 16)
                else:
                    # チャージ中：クールダウンに応じて水色のゲージが増えていく
                    # (150 - cooldown) / 150 で溜まり具合を計算
                    charge_pct = (150 - self.boost_cooldown) / 150
                    fill_w = charge_pct * (gw - 2)
                    col = 11 if self.boost_cooldown == 0 else 12 # 溜まったら明るい水色
                    pyxel.rect(gx + 1, gy + 1, fill_w, gh - 2, col)
                    pyxel.text(gx - 25, gy, "READY", 7 if self.boost_cooldown == 0 else 5)
                
            if self.state == self.STATE_PAUSE:
                self.draw_pause_overlay()

    def draw_pause_overlay(self):
        # 中央のメニュー枠
        mw, mh = 140, 90
        mx, my = (pyxel.width - mw) // 2, (pyxel.height - mh) // 2
        
        pyxel.rect(mx, my, mw, mh, 0)      # 黒い背景
        pyxel.rectb(mx, my, mw, mh, 7)     # 白い枠線
        
        # テキスト表示
        pyxel.text(mx + 60, my + 10, "PAUSED", 10)
        
        # 操作説明
        line_y = my + 30
        pyxel.text(mx + 10, line_y,      "- UP/DOWN : ACCEL/BRAKE", 7)
        pyxel.text(mx + 10, line_y + 10, "- SPACE   : NITRO BOOST", 10)
        
        if not self.is_automatic:
            pyxel.text(mx + 10, line_y + 20, "- Q / E   : GEAR CHANGE", 11)
        else:
            pyxel.text(mx + 10, line_y + 20, "- AUTO TRANSMISSION ON", 3)
        
        pyxel.text(mx + 30, my + 65, "PRESS [R] TO RESTART", 6)
        pyxel.text(mx + 27, my + 75, "PRESS [ESC] TO RESUME", 6)

    def draw_confetti(self, x, y, size, col, angle):
        """四角形の4つの角を計算して線で結ぶ（塗りつぶしは中央に点を打つ）"""
        rad = math.radians(angle)
        s, c = math.sin(rad), math.cos(rad)
        half = size / 2
        
        # 四隅の相対座標
        pts = [
            (-half * c - half * s, -half * s + half * c),
            ( half * c - half * s,  half * s + half * c),
            ( half * c + half * s,  half * s - half * c),
            (-half * c + half * s, -half * s - half * c)
        ]
        
        # 絶対座標に変換して線で描画
        for i in range(4):
            x1, y1 = x + pts[i][0], y + pts[i][1]
            x2, y2 = x + pts[(i + 1) % 4][0], y + pts[(i + 1) % 4][1]
            pyxel.line(x1, y1, x2, y2, col)
        
        # 簡易塗りつぶし（中心を塗りつぶす）
        pyxel.pset(x, y, col)


    def draw_title_screen(self):
        for i in range(10):
            y = (pyxel.frame_count * 2 + i * 20) % 150
            pyxel.line(0, y, 200, y, 1)
        pyxel.text(75, 700, "REAL DRIVING SIMULATER",10)
        pyxel.blt(-27, 40, 2, 0, 0, 255, 30, 229, scale= 0.7)
        pyxel.text(55, 70, "REAL DRIVING SIMULATER",10)
        if (pyxel.frame_count // 15) % 2 == 0:
            pyxel.text(72, 100, "PUSH SPACE KEY", 7)

    def draw_menu_screen(self):
        pyxel.rectb(20, 20, 160, 110, 7)
        pyxel.text(90, 35, "MENU", 10)
        pyxel.text(41, 90, f"DISTANCE: {self.goal_distance}km(UP/DOWN TO ADJUST)", 11)
        at_mt_text = "AT (AUTOMATIC)" if self.is_automatic else "MT (MANUAL)"
        pyxel.text(40, 65, f"[A] TRANSMISSION: {at_mt_text}", 10)
        if (pyxel.frame_count // 15) % 2 == 0:
            pyxel.text(60, 105, "SPACE: START GAME", 10)
        else:
            pyxel.text(60, 105, "SPACE: START GAME", 7)
        pyxel.text(60, 115, "ESC: BACK", 6)
        pyxel.text(40, 50, f"[C] CUSTOMIZE CAR COLOR", 14) # カスタマイズへの案内
        mode_text = "NIGHT" if self.is_night_mode else "DAY"
        mode_col = 12 if self.is_night_mode else 10 # 夜なら青、昼なら黄色っぽく
        pyxel.text(40, 77, f"[N]     : MODE [{mode_text}]", mode_col)

    def draw_customize_screen(self):
        pyxel.rectb(20, 20, 160, 110, 14)
        pyxel.text(75, 30, "CAR CUSTOMIZE", 14)
        
        # 色見本
        colors = [195, 12, 10, 11, 14]
        for i, col in enumerate(colors):
            pyxel.rect(40 + i*25, 50, 20, 20, col)
            pyxel.text(48 + i*25, 75, str(i+1), 7)
        
        # 現在の車のプレビュー
        pyxel.text(60, 95, "CURRENT COLOR:", 7)
        pyxel.rect(117, 93, 21, 16, 13)
        pyxel.pal(195, self.car_color)
        pyxel.blt(103, 90, 0, 0, 0, 50, 24, 229,scale=0.5)
        pyxel.text(60, 115, "PRESS [ESC] TO BACK", 6)

    
    
    def draw_single_object(self, obj, obj_y_screen, horizon):
        obj_perspective = (obj_y_screen - horizon) / (pyxel.height - horizon)
        night_visibility = 0.4 if self.is_night_mode else 0.05
        
        if night_visibility < obj_perspective < 1.0:
            curve_off = self.curve_val * (1 - obj_perspective)**3 * 80
            road_center_at_y = (pyxel.width / 2) + curve_off - (self.car_x * obj_perspective)
            current_road_half_width = (10 + (obj_perspective * 100) * 1.5)
            side = 1 if obj["margin_x"] > 0 else -1
            if obj["type"] == "sign":
                # 縁石の幅(edge_w)を考慮して少し外側に配置
                edge_w = 5 * obj_perspective + 3
                # 縁石の端 + わずかなマージン（遠近感を考慮）
                offset_from_center = current_road_half_width + edge_w + (2 * obj_perspective)
                obj_x = road_center_at_y + (offset_from_center * side)
            else:
                # 木は従来通り、ランダムなマージンを持たせる
                obj_x = road_center_at_y + (current_road_half_width * side) + (obj["margin_x"] * obj_perspective)
            
            # スケール制限
            adjusted_perspective = math.pow(obj_perspective, 1.2)
            raw_scale = adjusted_perspective * obj["size"] * 2.5
            MAX_SCALE = 2.5
            scale = min(raw_scale, MAX_SCALE)
            
            # 描画処理 (tree / sign)
            if obj["type"] == "tree":
                trunk_w, trunk_h = max(1, int(4 * scale)), max(1, int(12 * scale))
                leaf_s = max(1, int(10 * scale))
                pyxel.rect(obj_x - trunk_w // 2, obj_y_screen - trunk_h, trunk_w, trunk_h, 4)
                pyxel.tri(obj_x - leaf_s, obj_y_screen - trunk_h, 
                          obj_x + leaf_s, obj_y_screen - trunk_h, 
                          obj_x, obj_y_screen - trunk_h - leaf_s * 2, 3)
            else:
                pole_h = max(1, int(20 * scale))
                sign_w, sign_h = max(2, int(12 * scale)), max(2, int(8 * scale))
                pyxel.rect(obj_x - 1, obj_y_screen - pole_h, max(1, int(2 * scale)), pole_h, 4)
                pyxel.rect(obj_x - sign_w // 2, obj_y_screen - pole_h, sign_w, sign_h, obj["color"])
                pyxel.rectb(obj_x - sign_w // 2, obj_y_screen - pole_h, sign_w, sign_h, 7)

            # --- 衝突判定とペナルティの分岐 ---
            if 0.75 < obj_perspective < 0.85:
                # 判定幅（車の中心からの距離）
                hit_range = 15 if obj["type"] == "tree" else 12
                
                if abs(obj_x - pyxel.width / 2) < hit_range:
                    if not self.is_spinning:
                        if obj["type"] == "tree":
                            # 【木】速度をゼロにする
                            self.velocity = 0
                            self.shake_amount = 8  # 衝撃大
                            # スピンさせて操作不能にする
                            self.is_spinning = True
                            self.spin_timer = 0
                        else:
                            self.velocity = max(self.velocity - 0.075, 0.05)
                            self.is_spinning = True
                            self.is_kanban = True
                            self.shake_amount = 4

    def draw_game_scene(self):
        # パレットのリセットと夜間モードの適用
        pyxel.pal()
        if self.is_night_mode:
            pyxel.pal(7, 13)
            pyxel.pal(6, 16)
            pyxel.pal(11, 3)
            pyxel.pal(10, 9)
            pyxel.pal(13, 1)
            pyxel.pal(34, 21)
            pyxel.pal(229, 5)
            pyxel.pal(194, 13)
            
        # 背景（空）の描画
        sky_color = 16 if self.is_night_mode else 6
        pyxel.rect(0, 0, pyxel.width, 60, sky_color)

        # 雲の描画
        for c in sorted(self.clouds, key=lambda x: x["depth"]):
            scale = 0.5 + (c["depth"] * 0.5)
            pyxel.blt(c["x"] - (c["orig_w"]*scale)/2, c["y"], 1, c["u"], c["v"], c["orig_w"], c["orig_h"], 0)

        horizon = 60
        
        # --- 1. 描画対象をすべて収集してソートする準備 ---
        # p は 0.0 (地平線) から 1.0 (画面最下部) までの遠近係数
        render_queue = []

        # 道路オブジェクト（木・看板）の登録
        current_tree_span = 120.0
        for obj in self.road_objects:
            rel_depth = (obj["depth"] - self.speed) % current_tree_span
            # 奥行きを画面上のy座標から逆算してp値を算出
            obj_y_screen = pyxel.height - (rel_depth * 10)
            p = (obj_y_screen - horizon) / (pyxel.height - horizon)
            if 0 < p < 1.2: # 少し手前まで許容
                render_queue.append({'type': 'obj', 'p': p, 'data': obj, 'y': obj_y_screen})

        # ライバル車の登録
        max_view_distance = 500.0
        for rival in self.rival_cars:
            if 0 < rival["depth"] < max_view_distance:
                raw_p = 1.0 - (rival["depth"] / max_view_distance)
                p = math.pow(raw_p, 1.5) * 0.9 + 0.1
                render_queue.append({'type': 'rival', 'p': p, 'data': rival})

        # 自車の登録 (固定の奥行き p=0.85 付近に配置)
        render_queue.append({'type': 'player', 'p': 0.85})

        # 奥行き(p)が小さい順（遠い順）にソート
        render_queue.sort(key=lambda x: x['p'])

        # --- 2. 道路（地面）の描画 ---
        for y in range(horizon, pyxel.height):
            perspective = (y - horizon) / (pyxel.height - horizon)
            if perspective <= 0: continue
            
            seg = (1 / perspective) + (self.speed * 2)
            is_white_seg = (int(seg) % 2 == 0)
            
            current_grass_col = 34
            current_road_col = 13
            current_line_col = 7 if is_white_seg else 13
            current_edge_col = 7 if is_white_seg else 8

            if self.is_night_mode:
                if perspective < 0.3:
                    current_grass_col, current_road_col, current_line_col, current_edge_col = 21, 1, 13, 6
                elif perspective < 0.5:
                    current_grass_col, current_road_col, current_line_col = 21, 1, 13
                    current_edge_col = 13 if is_white_seg else 2

            curve_offset = self.curve_val * (1 - perspective)**3 * 80
            road_width = 10 + (perspective * 100) * 1.5
            center_x = (pyxel.width / 2) + curve_offset - (self.car_x * perspective)
            edge_w = 5 * perspective + 3

            # 地面・道路のライン描画
            if self.is_night_mode and perspective < 0.3:
                pyxel.rect(0, y, pyxel.width, 1, 22)
            else:
                pyxel.rect(0, y, pyxel.width, 1, current_grass_col)
            
            pyxel.rect(center_x - road_width, y, road_width * 2, 1, current_road_col)
            pyxel.rect(center_x - road_width - edge_w, y, edge_w, 1, current_edge_col)
            pyxel.rect(center_x + road_width, y, edge_w, 1, current_edge_col)
            pyxel.rect(center_x - 1, y, 2, 1, current_line_col)

        # --- 3. ソートされたオブジェクト・車の描画 ---
        for item in render_queue:
            p = item['p']
            y_draw = horizon + (p * (pyxel.height - horizon))
            c_off = self.curve_val * math.pow(1 - p, 3) * 80
            
            if item['type'] == 'obj':
                # 道路オブジェクト描画
                self.draw_single_object(item['data'], item['y'], horizon)
                
            elif item['type'] == 'rival':
                # ライバル車描画
                rival = item['data']
                riv_x = (pyxel.width / 2) + c_off - (self.car_x * p) + (rival["offset_x"] * p)
                
                # 向きの制御
                if self.curve_val > 0.2: riv_u, riv_w = 50, 26
                elif self.curve_val < -0.2: riv_u, riv_w = -50, 26
                else: riv_u, riv_w = 49, 0
                if rival.get("is_blown"): riv_u = random.choice([0, 50, -50])

                pyxel.pal(195, rival["col"])
                draw_scale = p * 1.5
                pyxel.blt(riv_x - (abs(riv_w) * draw_scale) / 2, y_draw - (24 * draw_scale), 
                          0, 0, riv_w, riv_u, 24, 229, 0, draw_scale)
                pyxel.pal()
                
                # 衝突判定（自車のp値付近のみ）
                if 0.70 < p < 0.95:
                    if not rival["is_blown"] and abs(riv_x - pyxel.width/2) < 20:
                        if not self.is_spinning:
                            self.velocity *= 0.5
                            self.is_spinning = True
                            self.is_kanban = True
                            self.spin_timer = 0
                            self.shake_amount = 10
                            rival["is_blown"] = True
                            rival["speed_kmh"] = 270
                            rival["blown_timer"] = 10

            elif item['type'] == 'player':
                # 自車のライト（夜間のみ）
                if self.is_night_mode:
                    light_center_x, light_y_base = pyxel.width / 2, 110
                    swing = -15 if pyxel.btn(pyxel.KEY_LEFT) else 15 if pyxel.btn(pyxel.KEY_RIGHT) else 0
                    for i in range(1, 9):
                        w = i * 4
                        target_x = light_center_x + (swing * (i / 10))
                        ly = light_y_base - (i * 3)
                        pyxel.line(target_x - w, ly, target_x + w, ly, 10)
                        if i < 5: pyxel.line(target_x - w//2, ly, target_x + w//2, ly, 7)

                # 自車本体の描画
                pyxel.pal(195, self.car_color)
                # 自車の座標は 95 で固定（リストのソート順により前後が決定される）
                pyxel.blt(pyxel.width/2 - 25, 95, 0, 0, self.w, self.u, 24, 229)
                if self.is_braking:
                    pyxel.rect(pyxel.width/2 - 14, 110, 5, 2, 8)
                    pyxel.rect(pyxel.width/2 + 9, 110, 5, 2, 8)
                pyxel.pal()

        # エフェクト（風の粒子）
        for p_item in self.wind_particles:
            dx, dy = p_item["x"] - pyxel.width / 2, p_item["y"] - 40
            if dx*dx + dy*dy > 4900:
                pyxel.line(p_item["x"], p_item["y"], p_item["x"] - p_item["vx"] * 1.2, p_item["y"] - p_item["vy"] * 1.2, p_item["col"])

        # スタートシグナル
        if self.start_timer > 0:
            cx, cy = pyxel.width / 2, 40
            pyxel.rectb(cx - 25, cy - 10, 50, 20, 7)
            pyxel.rect(cx - 24, cy - 9, 48, 18, 0)
            col_l = 11 if 0 <= self.start_timer <= 10 else 8 if 10 < self.start_timer < 100 else 5
            col_m = 8 if 10 < self.start_timer < 70 else 11 if 0 <= self.start_timer <= 10 else 5
            col_r = 11 if 0 <= self.start_timer <= 10 else 8 if 10 < self.start_timer < 40 else 5
            pyxel.sounds[1].volumes[0] = 7
            if self.start_timer == 100:
                pyxel.play(1, 1)
            elif self.start_timer == 70:
                pyxel.play(1, 1)
            elif self.start_timer == 40:
                pyxel.play(1, 1)
            elif self.start_timer == 10:
                pyxel.sounds[1].notes[0] = 48
                pyxel.play(1, 1)
            pyxel.circ(cx - 15, cy, 6, col_l)
            pyxel.circ(cx, cy, 6, col_m)
            pyxel.circ(cx + 15, cy, 6, col_r)
        if self.rocket_text_timer > 0:
            pyxel.text(pyxel.width/2 - 35, 80, "ROCKET START!!", pyxel.frame_count % 16)
            self.rocket_text_timer -= 1
            if self.rocket_text_timer == 0:
                self.is_rocket_start = False
        if self.stall_timer > 0:
            pyxel.text(pyxel.width/2 - 30, 80, "ENGINE STALL!", 8)
            self.stall_timer -= 1
            if self.stall_timer == 0:
                self.is_stalled = False


        # UIの描画
        if not self.is_goal:
            self.draw_speedometer()
            current_time = max(0, self.frame_count / 30)
            ui_col = 10 if self.is_night_mode else 0
            pyxel.text(10, 20, f"TIME: {current_time:.2f}s", ui_col)
            pyxel.text(10, 10, f"DISTANCE: {self.odometer:05.2f}/{self.goal_distance}km", ui_col)
        else:
            s = "CONGRATULATIONS! GOAL!!"
            x_txt = pyxel.width / 2 - len(s) * 2
            pyxel.rect(x_txt - 10, pyxel.height / 2 - 35, len(s) * 4 + 20, 50, 0)
            pyxel.text(x_txt, pyxel.height / 2 - 30, s, 10)
            if self.is_new_record:
                if (pyxel.frame_count % 20) < 10:
                    pyxel.text(x_txt + 7, pyxel.height / 2 - 15, f"NEW RECORD: {self.goal_time:.2f} SEC", 7)
                else:
                    pyxel.text(x_txt + 7, pyxel.height / 2 - 15, f"NEW RECORD: {self.goal_time:.2f} SEC", 10)
            else:
                pyxel.text(x_txt + 7, pyxel.height / 2 - 15, f"GOAL TIME: {self.goal_time:.2f} SEC", 10)
            pyxel.text(x_txt + 7, pyxel.height / 2, "PUSH 'R' TO RESTART", 6)

        # リスポーン画面
        if self.is_respawning:
            pyxel.cls(0)
            pyxel.text(pyxel.width/2 - 30, pyxel.height/2, "RECOVERING...", 7)
    def draw_speedometer(self):
        mx, my = 170, 130  # メーターの中心位置
        r = 20             # 半径
        
        # --- 1. RPMメーター（背景を完全に塗りつぶす） ---
        # 隙間を埋めるため、0.1度刻みでループを回し、少し内側(r+2)から塗り始める
        # rangeではなくwhileを使って細かく刻む
        deg = 180.0
        while deg <= 360.0:
            rad = math.radians(deg)
            # 内側の境界をr+2、外側をr+11に設定
            x1 = mx + math.cos(rad) * (r + 2)
            y1 = my - 1 + math.sin(rad) * (r + 2)
            x2 = mx + math.cos(rad) * (r + 11)
            y2 = my - 1 + math.sin(rad) * (r + 11)
            pyxel.line(x1, y1, x2, y2, 0)
            deg += 0.1
        # self.rpm (0.0~1.0) を 0~180度の範囲に変換
        # これにより、180度(開始点) + 180度 = 最大360度 に固定されます
        rpm_angle_range = max(0, min(int(self.rpm * 180), 180))
        
        for i in range(rpm_angle_range):
            rad = math.radians(180 + i)
            # インジケーターの太さを描画
            for thick in range(4, 10):
                px = mx + math.cos(rad) * (r + thick)
                py = my - 1 + math.sin(rad) * (r + thick)
                # 色の変化（150度/80%以上で赤）
                col = 8 if i > 150 else (10 if i > 110 else 11)
                pyxel.pset(px, py, col)
        # --- 2. スピードメーター ---
        # タコメーターとの接続部を綺麗にするため、スピードメーターの外枠(0番)を先に描く
        pyxel.circ(mx, my, r + 2, 0)
        pyxel.circ(mx, my, r, 5)
        
        # 目盛り
        for a in range(135, 406, 45):
            rad = math.radians(a)
            pyxel.line(mx + math.cos(rad)*(r-3), my + math.sin(rad)*(r-3), 
                       mx + math.cos(rad)*r, my + math.sin(rad)*r, 7)
            
        # 針
        angle = 135 + (self.velocity / 0.6) * 270
        rad = math.radians(angle)
        pyxel.line(mx, my, mx + math.cos(rad)*(r-2), my + math.sin(rad)*(r-2), 8)
        
        # 中心点と速度
        pyxel.circ(mx, my, 2, 7)
        pyxel.text(mx - 15, my + 5, f"{self.kilometer:3}km/h", 7)

        is_redzone = self.rpm > 0.85
        
        # 点滅ロジック: 3フレームごとに表示/非表示を切り替える（激しい点滅）
        # pyxel.frame_count % 6 < 3 とすることで、高速にチカチカする
        show_gear = not is_redzone or (pyxel.frame_count % 6 < 3)

        # ギアの背景枠
        pyxel.rect(mx - 4, my - 15, 9, 9, 0)

        if show_gear:
            # レッドゾーンなら点灯色は赤(8)、そうでなければ通常色(7 or 10)
            gear_col = 8 if is_redzone else (10 if self.rpm > 0.7 else 7)
            pyxel.text(mx - 2, my - 13, f"{self.gear + 1}", gear_col)
            
        # レッドゾーン時は「SHIFT UP!」と小さく表示
        if is_redzone and (pyxel.frame_count % 10 < 5):
            if self.gear != 4:
                pyxel.text(mx - 18, my - 22, "SHIFT UP!", 8)
        #ベストタイム表示
        bx, by = 130, 138
        dist = self.goal_distance
        best = self.best_times.get(dist)
        
        if self.is_night_mode:
            pyxel.text(bx+25, by - 110, f"BEST({dist}km):", 7)
        else:
            pyxel.text(bx+25, by - 110, f"BEST({dist}km):", 0)
        if best is not None:
            # 純粋な秒数表示に変更
            pyxel.text(bx + 35, by - 100, f"{best:.2f}s", 10) 
        else:
            pyxel.text(bx + 35, by - 100, "---.--s", 5)

App()