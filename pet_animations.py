from random import Random
from common_imports import *
from collections import defaultdict

class PetAnimations:

    def __init__(self, pet_widget):          
        self._load_dialog_file()  # 确保加载对话文件
        if not hasattr(self, 'dialog'):
            self.dialog = ["你好!", "今天过得怎么样?", "我是一只可爱的桌宠!"]
            
        self.pet = pet_widget
        self._animation_cache = {}
        self._animation_pool = AnimationPool()
        self._preload_animations()
        self._init_animation_system()

    def _init_animation_system(self):
        """初始化动画系统（移除边界限制）"""
        self.screen_geometry = QApplication.desktop().availableGeometry()
        self._current_animations = []
        self._is_animating = False
        self.current_direction = random.choice([-1, 1])
        # 移除 margin 相关设置
        self._load_dialog_file()
        QApplication.desktop().screenCountChanged.connect(self._update_screen_geometry)

    def _load_dialog_file(self):
        try:
            with open("config/talk.txt", "r", encoding="utf-8") as f:
                text = f.read()
                if text.strip():  # 检查文件内容是否为空
                    self.dialog = [line.strip() for line in text.split("\n") if line.strip()]
        except FileNotFoundError:
            logging.warning("talk.txt文件未找到，使用默认问候语")
        except UnicodeDecodeError:
            logging.error("talk.txt文件编码错误，请使用UTF-8格式")
        except Exception as e:
            logging.error(f"加载对话文件出错: {str(e)}")

    def play(self, anim_name):
        """增强的动画播放方法（抗干扰）"""
        print(f"尝试播放动画: {anim_name}")
        print(f"当前movie状态: {self.current_movie.state() if hasattr(self, 'current_movie') else 'None'}")
        if not hasattr(self, '_animation_cache'):
            return
        
        # 强制停止可能存在的残留动画
        if hasattr(self, 'current_movie') and self.current_movie:
            self.current_movie.stop()
    
        # 重新加载动画（防止拖动导致资源释放）
        if anim_name not in self._animation_cache:
            self._preload_animations()
    
        if anim_name in self._animation_cache:
            self.current_movie = self._animation_cache[anim_name]
            self.pet.pet_image.setMovie(self.current_movie)
            self.current_movie.start()
            print(f"动画恢复: {anim_name}")  # 调试输出
    
    def _preload_animations(self):
        """更健壮的动画预加载"""
        for name, path in self.pet.animation_bindings.items():
            try:
                full_path = os.path.join(os.path.dirname(__file__), path)
                if os.path.exists(full_path):
                    movie = QMovie(full_path)
                    movie.setCacheMode(QMovie.CacheAll)
                    movie.setScaledSize(QSize(200, 200))
                    # 强制设置循环模式（防止意外停止）
                    movie.setCacheMode(QMovie.CacheAll)
                    movie.start()  # 预启动
                    self._animation_cache[name] = movie
            except Exception as e:
                print(f"动画加载失败 {name}: {str(e)}")

    def _teleport_to_random_position(self):
        """使用对象池优化传送动画"""
        sequence = self._anim_pool.get_sequential_group()
        
        # 从池中获取动画对象
        fade_out = self._anim_pool.get_opacity_animation(self)
        fade_out.setDuration(500)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        
        move = self._anim_pool.get_pos_animation(self)
        move.setDuration(0)
        move.setStartValue(self.pet.pos())
        move.setEndValue(self._get_random_position())
        
        fade_in = self._anim_pool.get_opacity_animation(self)
        fade_in.setDuration(500)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        
        sequence.addAnimation(fade_out)
        sequence.addAnimation(move)
        sequence.addAnimation(fade_in)
        sequence.start()

    def _update_screen_geometry(self):
        self._screen_geometry = QApplication.desktop().availableGeometry()

    def get_random_greeting(self):
        return random.choice(self.dialog)  #返回固定语句
    
    def _ensure_screen_geometry(self):
        if not hasattr(self, 'screen_geometry'):
            self.screen_geometry = QApplication.desktop().availableGeometry()
    
    def _check_boundary(self, pos):
        """使用更精确的边界检测"""
        screen_rect = QApplication.desktop().availableGeometry()
        margin = self.margin
        rect = self.pet.geometry()  # 改为通过 pet 获取 geometry
    
        new_x = min(max(pos.x(), margin), screen_rect.width() - rect.width() - margin)
        new_y = min(max(pos.y(), margin), screen_rect.height() - rect.height() - margin)
    
        return QPoint(new_x, new_y)

    def request_animation(self, anim_func, priority=0):
        """请求播放动画，高优先级可中断低优先级动画"""
        if not self.animations_enabled:
            return
        
        if self._current_priority > priority and self._is_animating:
            return  # 当前有更高优先级动画运行中
        
        self._current_priority = priority
        self._stop_current_animations()
        anim_func()

    def _is_at_boundary(self, pos=None):
        if pos is None:
            pos = self.pet.pos()
    
        checked_pos = self._check_boundary(pos)
        is_boundary = pos != checked_pos
    
        if is_boundary:
            print(f"边界检测: 当前位置 {pos} 需要调整到 {checked_pos}")
    
        return is_boundary
    
    def _handle_boundary(self):
        """边界处理逻辑（优化版）"""
        if self._is_animating:
            return
        
        self._is_animating = True
        options = [
            self._bounce_back_animation,
            self._teleport_to_random_position,
            self._fade_and_reappear
        ]
    
        # 随机选择一个边界处理动画
        chosen_animation = random.choice(options)
        print(f"触发边界处理动画: {chosen_animation.__name__}")
        chosen_animation()

    def _get_valid_position_range(self):
        """获取有效的随机位置范围"""
        self._ensure_screen_geometry()
        max_x = max(self.margin, self.screen_geometry.width() - self.pet.width() - self.margin)
        max_y = max(self.margin, self.screen_geometry.height() - self.pet.height() - self.margin)
        return (self.margin, max_x, self.margin, max_y)
    
    def _teleport_to_random_position(self):
        """传送到随机位置"""
        self._stop_current_animations()
    
        min_x, max_x, min_y, max_y = self._get_valid_position_range()
        new_x = random.randint(min_x, max_x)
        new_y = random.randint(min_y, max_y)
        
        # 创建动画序列
        sequence = QSequentialAnimationGroup()
        
        # 淡出
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(500)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        
        # 移动
        move = QPropertyAnimation(self, b"pos")
        move.setDuration(0)
        move.setStartValue(self.pet.pos())
        move.setEndValue(QPoint(new_x, new_y))
        
        # 淡入
        fade_in = QPropertyAnimation(self, b"windowOpacity")
        fade_in.setDuration(500)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        
        sequence.addAnimation(fade_out)
        sequence.addAnimation(move)
        sequence.addAnimation(fade_in)
        
        sequence.finished.connect(self._animation_finished)
        sequence.start()
        self._current_animations.append(sequence)

    def random_walk(self):
        """自由行走动画（无边界检查）"""
        direction = "walkleft" if random.random() > 0.5 else "walkright"
        self.current_direction = -1 if direction == "walkleft" else 1
    
        # 播放行走动画
        self.play(direction)
    
        # 计算移动距离（不受限制）
        distance = random.randint(50, 150) * self.current_direction
        new_pos = self.pet.pos() + QPoint(distance, random.randint(-20, 20))
    
        # 创建移动动画
        walkanime = QPropertyAnimation(self.pet, b"pos")
        walkanime.setDuration(2000)
        walkanime.setEasingCurve(QEasingCurve.InOutSine)
        walkanime.setStartValue(self.pet.pos())
        walkanime.setEndValue(new_pos)
        walkanime.finished.connect(self._animation_finished)  # 确保连接完成回调
        walkanime.start()
        self._current_animations.append(walkanime)

    def random_phonewalk(self):
        """自由行走动画（无边界检查）"""
        direction = "phonewalkleft" if random.random() > 0.5 else "phonewalkright"
        self.current_direction = -1 if direction == "phonewalkleft" else 1
    
        # 播放行走动画
        self.play(direction)
    
        # 计算移动距离（不受限制）
        distance = random.randint(50, 150) * self.current_direction
        new_pos = self.pet.pos() + QPoint(distance, random.randint(-20, 20))
    
        # 创建移动动画
        walkanim = QPropertyAnimation(self.pet, b"pos")
        walkanim.setDuration(2000)
        walkanim.setEasingCurve(QEasingCurve.InOutSine)
        walkanim.setStartValue(self.pet.pos())
        walkanim.setEndValue(new_pos)
        walkanim.finished.connect(self._animation_finished)  # 确保连接完成回调
        walkanim.start()
        self._current_animations.append(walkanim)

    def jump_animation(self):
        """跳跃动画实现"""
        if self._is_animating or not self.pet.animations_enabled:
            return
    
        self._is_animating = True
        self.play("jump")  # 播放跳跃动画
    
        # 跳跃参数
        jump_height = 100  # 跳跃高度(像素)
        jump_duration = 800  # 跳跃持续时间(毫秒)
    
        # 创建跳跃动画序列
        jump_sequence = QSequentialAnimationGroup()
    
        # 上升动画
        up_anim = QPropertyAnimation(self.pet, b"pos")
        up_anim.setDuration(jump_duration // 2)
        up_anim.setEasingCurve(QEasingCurve.OutQuad)
        up_anim.setStartValue(self.pet.pos())
        up_anim.setEndValue(self.pet.pos() + QPoint(0, -jump_height))
    
        # 下降动画
        down_anim = QPropertyAnimation(self.pet, b"pos")
        down_anim.setDuration(jump_duration // 2)
        down_anim.setEasingCurve(QEasingCurve.InQuad)
        down_anim.setStartValue(self.pet.pos() + QPoint(0, -jump_height))
        down_anim.setEndValue(self.pet.pos())
    
        jump_sequence.addAnimation(up_anim)
        jump_sequence.addAnimation(down_anim)
    
        # 动画完成回调
        jump_sequence.finished.connect(self._animation_finished)
    
        # 添加到当前动画列表
        self._current_animations.append(jump_sequence)
        jump_sequence.start()

    def touch_animation(self) :
        """触摸动画实现"""
        if self._is_animating or not self.pet.animations_enabled:
            return
    
        self._is_animating = True
        self.play("touch") 
    
    def _bounce_back_animation(self):
        """反弹动画（修复版）"""
        self._stop_current_animations()
    
        current_pos = self.pet.pos()
        new_x = current_pos.x()
        new_y = current_pos.y()
    
        # 根据边界调整方向
        if current_pos.x() <= self.margin:
            new_x = current_pos.x() + 50
            self.current_direction = 1  # 向右
        elif current_pos.x() >= self.screen_geometry.width() - self.pet.width() - self.margin:
            new_x = current_pos.x() - 50
            self.current_direction = -1  # 向左
        
        if current_pos.y() <= self.margin:
            new_y = current_pos.y() + 50
        elif current_pos.y() >= self.screen_geometry.height() - self.pet.height() - self.margin:
            new_y = current_pos.y() - 50
    
        # 创建动画
        anim = QPropertyAnimation(self.pet, b"pos")
        anim.setDuration(800)
        anim.setEasingCurve(QEasingCurve.OutBounce)
        anim.setStartValue(current_pos)
        anim.setEndValue(QPoint(new_x, new_y))
        anim.finished.connect(self._animation_finished)
        anim.start()
        self._current_animations.append(anim)

    def _fade_and_reappear(self):
        """淡出并在附近重新出现"""
        self._stop_current_animations()
        
        # 计算新位置 (当前方向偏移)
        offset = 100 * self.current_direction
        new_pos = self._check_boundary(self.pet.pos() + QPoint(offset, 0))
        
        # 创建动画组
        group = QParallelAnimationGroup()
        
        # 移动动画
        move = QPropertyAnimation(self, b"pos")
        move.setDuration(1000)
        move.setEasingCurve(QEasingCurve.InOutQuad)
        move.setStartValue(self.pet.pos())
        move.setEndValue(new_pos)
        
        # 透明度动画
        opacity = QPropertyAnimation(self, b"windowOpacity")
        opacity.setDuration(1000)
        opacity.setKeyValues([
            (0.0, 1.0),
            (0.3, 0.2),
            (0.7, 0.2),
            (1.0, 1.0)
        ])
        
        group.addAnimation(move)
        group.addAnimation(opacity)
        group.finished.connect(self._animation_finished)
        group.start()
        self._current_animations.append(group)
    
    def _animation_finished(self):
        """动画完成回调 - 检查位置并处理"""
        self._is_animating = False
    
        # 检查是否在屏幕内
        if not self._is_in_screen():
            print("宠物移出屏幕，触发返回动画")
            self._start_return_animation()
        else:
            # 正常状态恢复
            self.play("idle")
            self.pet.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # 恢复鼠标交互

    def handle_click_interrupt(self):
        """处理鼠标点击中断动画"""
        if self._is_animating and self._is_in_screen():
            print("点击中断当前动画")
            self._stop_current_animations()
            self.play("idle")
     
    def _stop_current_animations(self):
        """停止当前所有动画"""
        for anim in self._current_animations:
            anim.stop()
            anim.deleteLater()
        self._current_animations.clear()
        self._is_animating = False
        # 停止当前电影
        if hasattr(self, 'current_movie') and self.current_movie:
            self.current_movie.stop()
        # 恢复鼠标交互
        self.pet.setAttribute(Qt.WA_TransparentForMouseEvents, False)
    
    def random_animation(self):
        """随机动画触发"""
        if not self._is_animating and self.pet.animations_enabled:
            # 先停止任何可能残留的动画
            self._stop_current_animations()
        
            # 随机选择动画类型
            animations = [
                self.random_walk,
                self.random_phonewalk,
                self.jump_animation,

            ]
            random.choice(animations)()

    def _check_visible_area(self):
        """检查是否在屏幕可视范围内"""
        screen_rect = QApplication.desktop().availableGeometry()
        if not screen_rect.intersects(self.pet.geometry()):
            print(f" 宠物移出屏幕 {self.pet.pos()}，将返回安全位置")
            return self._get_safe_position()
        return None
        pet_rect = self.pet.geometry()
    
        # 计算可见区域（保留20px边距）
        margin = 20
        visible_rect = screen_rect.adjusted(
            margin, margin, -margin, -margin
        )
    
        # 如果完全不可见，返回需要修正的位置
        if not visible_rect.intersects(pet_rect):
            return self._get_safe_position()
        return None

    def _get_safe_position(self):
        """获取安全的随机位置（确保在屏幕内）"""
        screen_rect = QApplication.desktop().availableGeometry()
        margin = 50  # 安全边距
        return QPoint(
            random.randint(margin, screen_rect.width() - self.pet.width() - margin),
            random.randint(margin, screen_rect.height() - self.pet.height() - margin)
        )
    def _start_return_animation(self):
        """启动返回屏幕的动画（此时禁用鼠标交互）"""
        self._is_animating = True
        self.pet.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 仅在此处禁用鼠标
    
        safe_pos = self._get_safe_position()
    
        # 创建动画组
        group = QSequentialAnimationGroup()
    
        # 淡出动画
        fade_out = QPropertyAnimation(self.pet, b"windowOpacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
    
        # 瞬移（不可见时移动）
        move = QPropertyAnimation(self.pet, b"pos")
        move.setDuration(0)
        move.setStartValue(self.pet.pos())
        move.setEndValue(safe_pos)
    
        # 淡入动画
        fade_in = QPropertyAnimation(self.pet, b"windowOpacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
    
        group.addAnimation(fade_out)
        group.addAnimation(move)
        group.addAnimation(fade_in)
    
        group.finished.connect(self._return_completed)
        group.start()
        self._current_animations.append(group)

    def _return_completed(self):
        """返回动画完成后恢复状态"""
        self._is_animating = False
        self.pet.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # 恢复鼠标交互
        self.play("idle")

    def _get_safe_position(self):
        """获取屏幕内的安全位置"""
        screen = QApplication.desktop().availableGeometry()
        margin = 50
        return QPoint(
            random.randint(margin, screen.width() - self.pet.width() - margin),
            random.randint(margin, screen.height() - self.pet.height() - margin)
        )

    def _stop_current_animations(self):
        """停止所有动画并清理状态"""
        for anim in self._current_animations:
            anim.stop()
            anim.deleteLater()
        self._current_animations.clear()
        self._is_animating = False
        self.pet.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def _is_in_screen(self):
        """检查宠物是否在屏幕范围内"""
        screen_rect = QApplication.desktop().availableGeometry()
        pet_rect = self.pet.geometry()
        margin = 20  # 安全边距
    
        # 检查是否完全在屏幕内（含安全边距）
        return screen_rect.adjusted(
            margin, margin, -margin, -margin
        ).contains(pet_rect)

 

    

    

class AnimationPool:
    def __init__(self):
        self._pool = defaultdict(list)
        self._active_animations = set()
        
    def get_animation(self, anim_type, target, property_name):
        if not self._pool[anim_type]:
            anim = QPropertyAnimation(target.pet if hasattr(target, 'pet') else target, property_name)
            anim.finished.connect(lambda: self.release_animation(anim_type, anim))
        else:
            anim = self._pool[anim_type].pop()
            anim.setTargetObject(target)
            anim.setPropertyName(property_name)
        
        self._active_animations.add(anim)
        return anim
        
    def release_animation(self, anim_type, anim):
        if anim in self._active_animations:
            anim.stop()
            self._active_animations.remove(anim)
            self._pool[anim_type].append(anim)
            
    def cleanup(self):
        for anim_list in self._pool.values():
            for anim in anim_list:
                anim.deleteLater()
        self._pool.clear()
        self._active_animations.clear()