# Copyright © 2025 Brandon Namgoong.
# Licensed under the GNU General Public License v3.0.
# Made for ICS3U1.

from pathlib import Path
from random import randint
from math import floor
import pygame

import utils, polygons, render

#-----------------------------------------------------------------------------
# globals
#-----------------------------------------------------------------------------

# pygame values
running: bool             = True
width: int                = 960 # max window size allowed is 1280 x 720
height: int               = 720
pageNum: int              = 0 # 0 is menu, 1 is level selection, 2 is game, 3 is settings, 4 is tutorial, 5 is credits
lastPage: int             = 0 # keep track of previous page visited
fps: int                  = 60 # global fps

# fonts
regularFont: Path         = utils.unifiedPath("res/fonts/regular.ttf")
boldFont: Path            = utils.unifiedPath("res/fonts/bold.ttf")

#-----------------------------------------------------------------------------
# game settings
#-----------------------------------------------------------------------------

musicState: int    = 3 # 0 is off, 1 is low, 2 is med, 3 is high
sfxState: int      = 3
invertXAxis: bool  = False

#-----------------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------------

def getGlRender() -> pygame.Surface:
    "Returns a Surface of the current OpenGL glfw context buffer."
    return pygame.image.frombytes(render.toBytes(), (width, height), "RGBA", flipped = True)

def getMouseX(invert: bool) -> int:
    "Gets the current mouse X position. Inverts if `invert` is `True`."
    return abs(invert * width - pygame.mouse.get_pos()[0])

def wrapMouse():
    """
    Wraps the cursor position around the left and right edges of the screen.

    Should be called periodically for correct function.
    """
    pos: tuple[int, int] = pygame.mouse.get_pos()
    if pos[0] == 0: # left edge
        pygame.mouse.set_pos(width - 5, pos[1]) # send to right edge
    elif pos[0] > width - 5: # right edge, buffer of 5 px for cursor width
        pygame.mouse.set_pos(1, pos[1]) # send to left edge plus 1 px

def topCenterTextPos(
    font: pygame.Font, text: str,
    topMargin: int
) -> tuple[int, int]:
    "Calculates and returns the position needed to blit center-aligned text based on top margin."
    return (
        width / 2 - font.size(text)[0] / 2,
        topMargin
    )

def topRightTextPos(
    font: pygame.Font, text: str,
    rightMargin: int, topMargin: int
) -> tuple[int, int]:
    "Calculates and returns the position needed to blit right-aligned text based on top right margin."
    size: tuple[int, int] = font.size(text)
    return (
        width - rightMargin - font.size(text)[0], # subtract by margin and size
        topMargin
    )

def bottomRightTextPos(
    font: pygame.Font, text: str,
    rightMargin: int, bottomMargin: int
) -> tuple[int, int]:
    "Calculates and returns the position needed to blit right-aligned text based on bottom right margin."
    size: tuple[int, int] = font.size(text)
    return (
        width - rightMargin - size[0], # subtract by margin and size
        height - bottomMargin - size[1]
    )

#-----------------------------------------------------------------------------
# anonymous math functions
#-----------------------------------------------------------------------------

# mouse tracking rotation based on snapping and initial offset
mouseTheta: int = lambda step = 5, offset = 0 : floor( # default values of 5º no offset
    ((360 * (getMouseX(invertXAxis) / width) + offset) % 360) / step
) * step

# random starting angle
randTheta: int = lambda step = 5 : randint(0, 360 // step) * step

# periodic linear "absolute-value" function
ctrlPos: float = lambda A, T, d, x : 4 * A * abs((x / T - d) % 1 - 0.5) - A

#-----------------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------------

class Button:
    """
    A class for wiping buttons with dynamic states on hover and on click.
    
    `pos` is the position of the button, anchored to the button's top left corner.
    `wipeTime` specifies the wipe time, in seconds, for the selected state sprite and is by default 170 ms.
    `clickSound` is the sound made when clicked, by default is the regular click sound.
    """
    def __init__(
        self,
        pos: tuple[int, int],
        normalState: Path, selectedState: Path, activeState: Path,
        wipeTime: float = 0.17, clickSound: Path = utils.unifiedPath("res/audio/sfx/button_click.mp3")
    ):
        self.__pos                   = pos # position on sreen
        self.__normalState           = pygame.image.load(normalState)
        self.__selectedState         = pygame.image.load(selectedState)
        self.__activeState           = pygame.image.load(activeState)
        self.__rect: pygame.Rect     = self.__normalState.get_rect(topleft = pos)

        self.__wipePerSecond: float  = self.__selectedState.width / wipeTime
        
        self.__hoverSound            = pygame.mixer.Sound(utils.unifiedPath("res/audio/sfx/button_hover.mp3"))
        self.__hoverSoundPlayed      = False # whether hover sound already played
        self.__clickSound            = pygame.mixer.Sound(clickSound)
        
        self.wipeProgress: float     = 0
        self.hovering: bool          = False # whether mouse is hovering button
        self.pushed: bool            = False # whether button is simply pressed
        self.clicked: bool           = False # whether button has actually been clicked after mouse up
    
    def update(self, dt: float):
        """
        Updates the button view based on mouse events. Should be called periodically.
        `dt` specifies the seconds since the last call.
        """
        self.clicked = False # set first thing
        if self.__rect.collidepoint(pygame.mouse.get_pos()): # check if mouse inside button
            self.hovering = True
            if not self.__hoverSoundPlayed:
                self.__hoverSound.set_volume(sfxState / 3)
                self.__hoverSound.play()
                self.__hoverSoundPlayed = True
            if pygame.mouse.get_pressed()[0]:
                # active state
                self.pushed = True
                self.clicked = False
                self.wipeProgress = self.__rect.width # reset wipe
                screen.blit(self.__activeState, self.__pos)
            else:
                # selected state
                self.clicked = self.pushed # clicked if previously pushed, not if not
                if self.wipeProgress < self.__rect.width:
                    self.wipeProgress = min(
                        self.wipeProgress + self.__wipePerSecond * dt, # constrain to maximum of button length
                        self.__rect.width
                    )
                if self.wipeProgress < self.__rect.width: # check again for other uses
                    self.__normalState.set_alpha(
                        255 * (1 - self.wipeProgress / self.__rect.width) # get as inverse percentage mapped to alpha range
                    )
                    screen.blit(self.__normalState, self.__pos)
                    screen.blit(
                        self.__selectedState, self.__pos,
                        pygame.Rect(
                            0, 0, self.wipeProgress, self.__rect.height
                        )
                    )
                else:
                    screen.blit(self.__selectedState, self.__pos)
        else:
            # normal state
            self.pushed = self.hovering = self.__hoverSoundPlayed = self.clicked = False
            if self.wipeProgress > 0:
                self.wipeProgress = max(
                    self.wipeProgress - self.__wipePerSecond * dt, # constrain to minimum of 0
                    0
                )
            if self.wipeProgress > 0: # check again to not draw width of 0
                self.__normalState.set_alpha(
                    255 * (1 - self.wipeProgress / self.__rect.width) # get as inverse percentage mapped to alpha range
                )
                screen.blit(self.__normalState, self.__pos)
                screen.blit(
                    self.__selectedState, self.__pos,
                    pygame.Rect(
                        0, 0, self.wipeProgress, self.__rect.height
                    )
                )
            else:
                self.__normalState.set_alpha(255)
                screen.blit(self.__normalState, self.__pos)
        if self.clicked:
            self.__clickSound.set_volume(sfxState / 3)
            self.__clickSound.play()

class CycleButton:
    """
    A class representing a button that cycles through multiple states.
    
    `pos` is the position of the button, anchored to the button's top left corner.
    `wipeTime` specifies the wipe time, in seconds, for the selected state sprite and is by default 170 ms.
    """
    def __init__(
        self,
        pos: tuple[int, int],
        normalStates: list[Path], selectedStates: list[Path], activeStates: list[Path],
        initCycleState: int, wipeTime: float = 0.17
    ):
        self.__buttons        = [ Button(
            pos, normalStates[i], selectedStates[i], activeStates[i], wipeTime
        ) for i in range(len(normalStates)) ]

        self.__wipeProgress   = 0.0 # value to transfer between buttons

        self.cycleState: int  = initCycleState # the state of the cycle, is an index for button set
    
    def update(self, dt: float):
        "Updates the cycle button."
        self.__buttons[self.cycleState].update(dt)
        self.__wipeProgress = self.__buttons[self.cycleState].wipeProgress
        if self.__buttons[self.cycleState].clicked: # if current button clicked
            self.__buttons[self.cycleState].clicked = False # ensure it is false before moving on
            self.__buttons[self.cycleState].pushed = False # this too
            self.cycleState = (self.cycleState + 1) % len(self.__buttons) # cycle through
            self.__buttons[self.cycleState].wipeProgress = self.__wipeProgress # transfer to new

class HoverItem:
    """
    A class representing a simple sprite with hover detection.
    
    `pos` is the position of the sprite, anchored to the sprite's top left corner.
    """
    def __init__(self, pos: tuple[int, int], sprite: Path):
        self.__pos     = pos
        self.__sprite  = pygame.image.load(sprite)
        self.__rect    = self.__sprite.get_rect(topleft = pos)

        self.hovering  = False # whether hovering
    
    def update(self, _):
        "Updates the button view based on mouse events. Should be called periodically."
        self.hovering = self.__rect.collidepoint(pygame.mouse.get_pos())
        screen.blit(self.__sprite, self.__pos)

class LevelSelector:
    """
    A class representing a level selector button, a higher level button type.
    
    `pos` is the position of the button, anchored to the button's top left corner.
    `levelName` is the name of the level (identical to the shape name of the level).
    """
    def __init__(self, pos: tuple[int, int], levelName: str):
        self.__locked: bool     = False
        self.__reqLevel: str    = ""
        self.__threshold: int   = 0

        self.__hoverText        = pygame.Font(regularFont, 24)

        self.name               = levelName
        self.play: bool         = False # whether play of level is requested

        # check for score unlock
        thresh = utils.thresholds[levelName] # kept as any data type
        if thresh == 0 or utils.getHighScore(thresh[0]) >= thresh[1]: # either always unlocked or threshold met
            self.item = Button(
                pos,
                utils.unifiedPath(f"res/sprites/buttons/levels/{levelName}_n.png"),
                utils.unifiedPath(f"res/sprites/buttons/levels/{levelName}_s.png"),
                utils.unifiedPath(f"res/sprites/buttons/levels/{levelName}_a.png"),
                clickSound = utils.unifiedPath("res/audio/sfx/play.mp3")
            )
        else: # level locked
            self.__locked = True
            self.__reqLevel = thresh[0]
            self.__threshold = thresh[1]
            self.item = HoverItem(
                pos, utils.unifiedPath("res/sprites/buttons/levels/locked.png")
            )
    
    def update(self, dt: float):
        """
        Updates the selector. Should be called periodically.
        `dt` specifies the seconds since the last call.
        """
        self.play = False
        self.item.update(dt)

        if not self.__locked and self.item.clicked: # check locked to not access clicked from HoverItem
            self.play = True
        if self.item.hovering: # hover text
            if self.__locked:
                screen.blit(
                    self.__hoverText.render(
                        f"{utils.friendlyNames[self.name]}\n\nunlock with score {self.__threshold} in {utils.friendlyNames[self.__reqLevel]}",
                        True, utils.uiColors["text"]
                    ),
                    (480, 160)
                )
            else:
                screen.blit(
                    self.__hoverText.render(
                        f"{utils.friendlyNames[self.name]}\n\nhigh score : {utils.getHighScore(self.name)}",
                        True, utils.uiColors["text"]
                    ),
                    (480, 160)
                )

class LifeManager:
    "Class for managing game lives."
    def __init__(self, pos: tuple[int, int], lifeNum: int):
        self.__pos          = pos
        self.__max          = lifeNum # maximum number of lives given

        self.__lifeSprite   = pygame.image.load(utils.unifiedPath("res/sprites/game/life.png"))
        self.__deathSirpte  = pygame.image.load(utils.unifiedPath("res/sprites/game/death.png"))

        self.__killSound    = pygame.mixer.Sound(utils.unifiedPath("res/audio/sfx/kill.mp3"))

        self.num            = lifeNum # current life num
    
    def killLife(self):
        """
        Subtracts a life.
        Does nothing if there are 0 lives.
        """
        self.num = max(self.num - 1, 0)
        self.__killSound.set_volume(sfxState / 3)
        self.__killSound.play()

    def update(self):
        """
        Updates the life manager. Should be called periodically.
        `dt` specifies the seconds since the last call.
        """
        newPos: list[int, int] = list(self.__pos)

        for i in range(self.num): # show lives
            screen.blit(
                self.__lifeSprite, tuple(newPos)
            )
            newPos[1] += self.__lifeSprite.height + 20
        for i in range(self.__max - self.num): # show deaths
            screen.blit(
                self.__deathSirpte, tuple(newPos)
            )
            newPos[1] += self.__lifeSprite.height + 20 # still use life sprite height for consistency

class VerticalTimer:
    """
    A class representing the timer bar.
    `time` is the timer time in seconds.
    """
    def __init__(
        self,
        pos: tuple[int, int],
        baseImage: Path, timerImage: Path,
        time: int
    ):
        self.__pos                   = pos
        self.__base: pygame.Surface  = pygame.image.load(baseImage)
        self.__bar: pygame.Surface   = pygame.image.load(timerImage)

        self.__width: int            = self.__bar.get_width()
        self.__height: int           = self.__bar.get_height()

        self.__perSecond: float      = self.__height / time
        self.__progress: float       = 0.0 # fraction of length

        self.__warnSound             = pygame.mixer.Sound(utils.unifiedPath("res/audio/sfx/warning.mp3"))
        self.__warnSoundPlayed       = False # whether sound already played
        
        self.restarted: bool         = False # whether the timer has just completed a full time
    
    def reset(self):
        "Resets the progress of the timer."
        self.__progress = 0
        self.__warnSoundPlayed = False # reset sound play status

    def update(self, dt: float):
        """
        Updates the timer. Should be called periodically.
        `dt` specifies the seconds since the last call.
        """
        # self.restarted = True if self.__progress + self.__perSecond * dt > self.__len else False
        self.restarted = False
        screen.blit(
            self.__base, self.__pos
        )

        self.__progress += self.__perSecond * dt
        if self.__progress > self.__height: # restart timer progress
            self.restarted = True
            self.__progress %= self.__height
            self.__warnSoundPlayed = False # reset sound play status
        
        # play warning
        if self.__progress >= 0.75 * self.__height and not self.__warnSoundPlayed:
            self.__warnSound.set_volume(sfxState / 3)
            self.__warnSound.play()
            self.__warnSoundPlayed = True # prevent sound from playing repeatedly
        
        # window.blit(self.__bar, self.__pos, pygame.Rect(0, 0, self.__progress, self.__height))
        screen.blit(
            self.__bar, self.__pos,
            pygame.Rect(
                0, 0, self.__width, self.__progress
            )
        )

#-----------------------------------------------------------------------------
# game page loops
#-----------------------------------------------------------------------------

def loadingPage():
    "The loading screen page."
    # splash
    splash: pygame.Surface = pygame.image.load(utils.unifiedPath("res/sprites/misc/splash.png"))

    # other
    alpha: int = 0
    sumt: float = 0
    dt: float = 0

    while True:
        # exit input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global running ; running = False
                return

        # go to menu if time exceeded
        if sumt >= 4:
            global pageNum ; pageNum = 0
            return

        # render
        if sumt > 0.5 and sumt <= 3: # fade in and rest from t = 0.5 to t = 3
            alpha = min(alpha + 255 * dt * 2, 255) # cap at 255
        elif sumt > 3: # fade out after t = 3
            alpha = max(alpha - 255 * dt * 2, 0) # min of 0
        splash.set_alpha(alpha)

        screen.fill("black")
        screen.blit(splash, (340, 257)) # at center

        # final
        pygame.display.flip()
        dt = clock.tick(fps) / 1000
        sumt += dt

def menuPage(bgShape: str) -> str | None:
    "The main menu page."
    # shape
    global lastPage
    shapeName: str = polygons.randomShape() if bgShape == None or lastPage == 2 else bgShape # conditions for new bg shape
    shape = polygons.extrude(polygons.get(shapeName))

    # buttons
    playBut = Button(
        (100, 300),
        utils.unifiedPath("res/sprites/buttons/menu/play_n.png"),
        utils.unifiedPath("res/sprites/buttons/menu/play_s.png"),
        utils.unifiedPath("res/sprites/buttons/menu/play_a.png")
    )
    settingsBut = Button(
        (100, 390),
        utils.unifiedPath("res/sprites/buttons/menu/settings_n.png"),
        utils.unifiedPath("res/sprites/buttons/menu/settings_s.png"),
        utils.unifiedPath("res/sprites/buttons/menu/settings_a.png")
    )
    tutorialBut = Button(
        (100, 480),
        utils.unifiedPath("res/sprites/buttons/menu/tutorial_n.png"),
        utils.unifiedPath("res/sprites/buttons/menu/tutorial_s.png"),
        utils.unifiedPath("res/sprites/buttons/menu/tutorial_a.png")
    )
    creditsBut = Button(
        (100, 570),
        utils.unifiedPath("res/sprites/buttons/menu/credits_n.png"),
        utils.unifiedPath("res/sprites/buttons/menu/credits_s.png"),
        utils.unifiedPath("res/sprites/buttons/menu/credits_a.png")
    )

    # others
    backdrop: pygame.Surface  = pygame.image.load(utils.unifiedPath("res/sprites/misc/backdrop.png"))
    versionText = pygame.Font(regularFont, 20)
    dt: float = 0

    # music
    if not pygame.mixer.music.get_busy() or lastPage == 2: # either not playing or just came from game page
        pygame.mixer.music.load(utils.unifiedPath("res/audio/menu.mp3")) # load
        pygame.mixer.music.play(-1) # loop indefinitely

    while True:
        # exit input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global running ; running = False
                return None

        # render
        screen.blit(backdrop)

        render.reset()
        render.setupScene()

        render.drawPolygon(
            shape["vertices"], shape["bases"], shape["quads"], shape["isConvex"],
            utils.uiColors["button_normal"],
            dx = 4, dz = -1, theta = mouseTheta()
        )

        render.finish()
        screen.blit(getGlRender())

        screen.blit( # logo
            pygame.image.load(utils.unifiedPath("res/sprites/misc/logo.png")),
            (100, 100)
        )
        screen.blit( # version text
            versionText.render(utils.versionString, True, utils.uiColors["text"]),
            bottomRightTextPos(versionText, utils.versionString, 30, 20)
        )

        playBut.update(dt)
        settingsBut.update(dt)
        tutorialBut.update(dt)
        creditsBut.update(dt)

        # post-render
        global pageNum
        if playBut.clicked:
            pageNum = 1 # go to level select
            lastPage = 0
            return shapeName
        if settingsBut.clicked:
            pageNum = 3 # go to settings
            lastPage = 0
            return shapeName
        if tutorialBut.clicked:
            pageNum = 4 # go to tutorial
            lastPage = 0
            return shapeName
        if creditsBut.clicked:
            pageNum = 5 # go to credits
            lastPage = 0
            return shapeName

        # final
        pygame.display.flip()
        dt = clock.tick(fps) / 1000

def levelsPage(bgShape: str) -> str | None:
    "The level selection page."
    # shape
    shape = polygons.extrude(polygons.get(bgShape))

    # buttons
    backBut = Button(
        (100, 100),
        utils.unifiedPath("res/sprites/buttons/back_n.png"),
        utils.unifiedPath("res/sprites/buttons/back_s.png"),
        utils.unifiedPath("res/sprites/buttons/back_a.png")
    )

    # selectors
    selectors = [
        LevelSelector((100, 210), "square"), LevelSelector((210, 210), "triangle"), LevelSelector((320, 210), "rectangle"),
        LevelSelector((100, 320), "hexagon"), LevelSelector((210, 320), "caret"), LevelSelector((320, 320), "slant"),
        LevelSelector((100, 430), "pentagon"), LevelSelector((210, 430), "en"), LevelSelector((320, 430), "kay"),
        LevelSelector((100, 540), "mta_arrow"), LevelSelector((210, 540), "pi"), LevelSelector((320, 540), "double_u"),
    ]

    # others
    backdrop: pygame.Surface  = pygame.image.load(utils.unifiedPath("res/sprites/misc/backdrop.png"))
    versionText = pygame.Font(regularFont, 20)
    dt: float = 0

    while True:
        # exit input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global running ; running = False
                return
        
        # render
        screen.blit(backdrop)

        render.reset()
        render.setupScene()

        render.drawPolygon(
            shape["vertices"], shape["bases"], shape["quads"], shape["isConvex"],
            utils.uiColors["button_normal"],
            dx = 4, dz = -1, theta = mouseTheta()
        )

        render.finish()
        screen.blit(getGlRender())

        screen.blit( # version text
            versionText.render(utils.versionString, True, utils.uiColors["text"]),
            bottomRightTextPos(versionText, utils.versionString, 30, 20)
        )

        backBut.update(dt)
        for sel in selectors: sel.update(dt)

        # post-render
        global pageNum, lastPage
        if backBut.clicked:
            pageNum = 0 # go to menu
            lastPage = 1
            return None
        for sel in selectors:
            if sel.play: # level chosen
                pageNum = 2
                lastPage = 1

                # unload music
                pygame.mixer.music.unload()

                return sel.name

        # final
        pygame.display.flip()
        dt = clock.tick(fps) / 1000

def gamePage(gameShape: str):
    "The game page."
    # game screen elements
    amp: int = 4 # absolute amplitude amount outward
    period: int = 3.5 # seconds

    control: dict = polygons.extrude(polygons.get(gameShape)) # currently controlling shape
    forward: bool = True # "forward" means SE-NW, the reverse means SW-NE
    controlX: int = not forward * amp # start in top left
    controlY: int = amp
    controlTheta: float = 0
    thetaOffset: int = randTheta() # init with random
    pt: float = 0 # period time; x-value of movement function

    colIndex: int = 0 # index of color of control

    tower: list[dict] = [] # tower representing the stacks of shapes on top of base in ascending order
    towerBase: dict = control # base of tower, set initially to the same as the control block
    stack: int = len(tower) # tower height

    lives = LifeManager(
        (790, 260), 3
    )
    timer = VerticalTimer(
        (900, 210),
        utils.unifiedPath("res/sprites/game/timer_base.png"),
        utils.unifiedPath("res/sprites/game/timer.png"),
        6
    )

    # text
    pauseText = pygame.Font(regularFont, 30)
    scoreText = pygame.Font(boldFont, 100)
    highScoreText = pygame.Font(regularFont, 20)

    # other
    backdrop: pygame.Surface  = pygame.image.load(utils.unifiedPath("res/sprites/misc/backdrop.png"))

    score: int = 0
    highScore: int = utils.getHighScore(gameShape)

    clicked: bool = False # whether screen clicked

    paused: bool = False # whether to go through pase menu loop
    gameover: bool = False # True once game lost

    dt: float = 0 # time since last loop

    pygame.mixer.music.load(utils.unifiedPath("res/audio/game.mp3"))
    pygame.mixer.music.play(-1)

    stackSound = pygame.mixer.Sound(utils.unifiedPath("res/audio/sfx/stack.mp3"))
    stackSound.set_volume(sfxState / 3)

    while True:
        # pre-input
        pygame.mouse.set_relative_mode(True) # hide, encase
        wrapMouse()
        clicked = False

        # input handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global running ; running = False
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    clicked = True
        
        # game over screen
        if gameover:
            def gameover():                
                # new high score?
                newHigh: bool = False

                if score > utils.getHighScore(gameShape):
                    utils.setHighScore(gameShape, score)
                    newHigh = True
                
                # blurred screen
                blurred: pygame.Surface = pygame.transform.gaussian_blur(screen, 20) # gaussian blur
                blurred.set_alpha(127) # around 50% alpha

                # buttons
                retryBut = Button(
                    (500, 290),
                    utils.unifiedPath("res/sprites/buttons/game/retry_n.png"),
                    utils.unifiedPath("res/sprites/buttons/game/retry_s.png"),
                    utils.unifiedPath("res/sprites/buttons/game/retry_a.png")
                )
                exitBut = Button(
                    (500, 380),
                    utils.unifiedPath("res/sprites/buttons/game/exit_n.png"),
                    utils.unifiedPath("res/sprites/buttons/game/exit_s.png"),
                    utils.unifiedPath("res/sprites/buttons/game/exit_a.png")
                )

                # other
                pygame.mixer.music.unload()

                dt: float = 0

                while True:
                    # pre-input
                    pygame.mouse.set_relative_mode(False) # release

                    # exit input
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            global running ; running = False
                            return
                    
                    # render
                    screen.fill("white")
                    screen.blit(blurred)

                    screen.blit(
                        scoreText.render(str(score), True, utils.uiColors["text"]),
                        topRightTextPos(scoreText, str(score), 500, 310)
                    )
                    if newHigh:
                        screen.blit(
                            highScoreText.render("new high!", True, utils.uiColors["text"]),
                            topRightTextPos(highScoreText, "new high!", 500, 410)
                        )
                    else:
                        screen.blit(
                            highScoreText.render(f"high score : {highScore}", True, utils.uiColors["text"]),
                            topRightTextPos(highScoreText, f"high score : {highScore}", 500, 410)
                        )

                    retryBut.update(dt)
                    exitBut.update(dt)

                    # post-render
                    global lastPage, pageNum
                    if retryBut.clicked:
                        lastPage = 2
                        pageNum = 2 # come back to this page again
                        return
                    if exitBut.clicked:
                        lastPage = 2
                        pageNum = 0 # go to menu
                        return

                    # final
                    pygame.display.flip()
                    dt = clock.tick(fps) / 1000
            
            gameover()
            return

        # pause submenu
        if paused:
            def paused() -> bool:
                # capture screne
                background: pygame.Surface = screen.copy()

                pygame.mixer.music.pause()

                # buttons
                resumeBut = Button(
                    (50, 100),
                    utils.unifiedPath("res/sprites/buttons/game/resume_n.png"),
                    utils.unifiedPath("res/sprites/buttons/game/resume_s.png"),
                    utils.unifiedPath("res/sprites/buttons/game/resume_a.png"),
                    clickSound = utils.unifiedPath("res/audio/sfx/resume.mp3")
                )
                exitBut = Button(
                    (50, 190),
                    utils.unifiedPath("res/sprites/buttons/game/exit_n.png"),
                    utils.unifiedPath("res/sprites/buttons/game/exit_s.png"),
                    utils.unifiedPath("res/sprites/buttons/game/exit_a.png")
                )

                # other
                dt: float = 0

                # sound
                pauseSound = pygame.mixer.Sound(utils.unifiedPath("res/audio/sfx/pause.mp3"))
                pauseSound.set_volume(sfxState / 3)
                pauseSound.play()

                while True:
                    # pre-input
                    pygame.mouse.set_relative_mode(False) # release

                    # exit input
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            global running ; running = False
                            return
                    
                    # render
                    screen.blit(background)

                    resumeBut.update(dt)
                    exitBut.update(dt)

                    # post-render
                    global lastPage, pageNum
                    if resumeBut.clicked:
                        pygame.mixer.music.unpause()
                        return True
                    if exitBut.clicked:
                        lastPage = 2
                        pageNum = 0 # go to menu

                        # unload music
                        pygame.mixer.music.unload()

                        return False

                    # final
                    pygame.display.flip()
                    dt = clock.tick(fps) / 1000

            cont: bool = paused() # whether to continue
            paused = False
            if cont: continue
            else: return

        # pre-render
        if len(tower) > 7:
            tower.pop(0) # shave off bottom
        stack = len(tower)

        if forward: # SE-NW
            controlX = ctrlPos(amp, period, -0.5, pt) # d = -1/2 period shift
        else: # SW-NE
            controlX = ctrlPos(amp, period, 0, pt)
        controlY = ctrlPos(amp, period, 0, pt) # d = 0 period shift
        controlTheta = mouseTheta(offset = thetaOffset) # apply offset of random angle

        # render
        screen.blit(backdrop)

        render.reset()
        render.setupScene()

        render.drawPolygon( # render control block
            control["vertices"], control["bases"], control["quads"], control["isConvex"],
            utils.blockColors[colIndex],
            dx = controlX, dy = controlY, theta = controlTheta
        )
        render.drawPolygon( # render tower base
            towerBase["vertices"], towerBase["bases"], towerBase["quads"], towerBase["isConvex"],
            (64, 64, 64), # 25% gray
            dz = -1 - stack, theta = 45 # only tower base is rotated because it is the original shape
        )
        for i in range(stack): # render rest of tower stack
            newColIndex = (colIndex - stack + i) % len(utils.blockColors)
            render.drawPolygon(
                tower[i]["vertices"], tower[i]["bases"], tower[i]["quads"], tower[i]["isConvex"],
                utils.blockColors[newColIndex],
                dz = i - stack # move down based on height
            )

        render.finish()
        screen.blit(getGlRender())

        screen.blit(
            pauseText.render("press ESC to pause", True, utils.uiColors["text"]),
            (50, 50)
        )
        screen.blit(
            scoreText.render(str(score), True, utils.uiColors["primary"]),
            topCenterTextPos(scoreText, str(score), 80)
        )
        screen.blit(
            highScoreText.render(f"high score : {highScore}", True, utils.uiColors["text"]),
            topCenterTextPos(highScoreText, f"high score : {highScore}", 50)
        )

        lives.update()
        timer.update(dt)

        # post-render        
        if clicked: # if regular stack click
            timer.reset() # reset timer

            # calculate new shape
            render.reset()
            render.setupScene(xtheta = 0) # look at FLAT ON
            if stack == 0: # if only base
                newBase = polygons.spacialTransform(towerBase["polygon"], render.getMatrix(
                    0, 0, -1, 45 # rotated 45 because base
                ))
            else:
                newBase = polygons.spacialTransform(tower[-1]["polygon"], render.getMatrix(
                    0, 0, -1, 0
                ))
            render.reset()
            render.setupScene(xtheta = 0)
            newControl = polygons.spacialTransform(control["polygon"], render.getMatrix(
                controlX, controlY, 0, controlTheta # use current control transformations
            ))
            control = polygons.extrude( # get new shape
                polygons.andPolygons(
                    newBase, newControl
                )
            )
            tower.append(control) # add new control as new layer to tower

            # new movement
            pt = 0
            forward = not forward
            thetaOffset = randTheta()

            colIndex = (colIndex + 1) % len(utils.blockColors)

            # sound
            stackSound.play()
        
        if len(control["vertices"]) < 3 or lives.num == 0: # lose conditions; either no more drawable polygon or no more lives
            gameover = True

        if timer.restarted: # if time out for placing
            lives.killLife() # remove 1 life

        if clicked and not gameover: # add to score only when it should
            score += 1

        # final
        pygame.display.flip()
        dt = clock.tick(fps) / 1000
        pt = (pt + dt) % period

def settingsPage(bgShape: str):
    "The settings page."
    # shape
    shape = polygons.extrude(polygons.get(bgShape))

    # buttons
    backBut = Button(
        (100, 100),
        utils.unifiedPath("res/sprites/buttons/back_n.png"),
        utils.unifiedPath("res/sprites/buttons/back_s.png"),
        utils.unifiedPath("res/sprites/buttons/back_a.png")
    )
    global musicState, sfxState, invertXAxis
    musicBut = CycleButton(
        (350, 240),
        [
            utils.unifiedPath("res/sprites/buttons/settings/off_fourstate_n.png"),
            utils.unifiedPath("res/sprites/buttons/settings/low_n.png"),
            utils.unifiedPath("res/sprites/buttons/settings/med_n.png"),
            utils.unifiedPath("res/sprites/buttons/settings/high_n.png")
        ],
        [
            utils.unifiedPath("res/sprites/buttons/settings/off_fourstate_s.png"),
            utils.unifiedPath("res/sprites/buttons/settings/low_s.png"),
            utils.unifiedPath("res/sprites/buttons/settings/med_s.png"),
            utils.unifiedPath("res/sprites/buttons/settings/high_s.png")
        ],
        [
            utils.unifiedPath("res/sprites/buttons/settings/off_fourstate_a.png"),
            utils.unifiedPath("res/sprites/buttons/settings/low_a.png"),
            utils.unifiedPath("res/sprites/buttons/settings/med_a.png"),
            utils.unifiedPath("res/sprites/buttons/settings/high_a.png")
        ],
        musicState
    )
    sfxBut = CycleButton(
        (350, 340),
        [
            utils.unifiedPath("res/sprites/buttons/settings/off_fourstate_n.png"),
            utils.unifiedPath("res/sprites/buttons/settings/low_n.png"),
            utils.unifiedPath("res/sprites/buttons/settings/med_n.png"),
            utils.unifiedPath("res/sprites/buttons/settings/high_n.png")
        ],
        [
            utils.unifiedPath("res/sprites/buttons/settings/off_fourstate_s.png"),
            utils.unifiedPath("res/sprites/buttons/settings/low_s.png"),
            utils.unifiedPath("res/sprites/buttons/settings/med_s.png"),
            utils.unifiedPath("res/sprites/buttons/settings/high_s.png")
        ],
        [
            utils.unifiedPath("res/sprites/buttons/settings/off_fourstate_a.png"),
            utils.unifiedPath("res/sprites/buttons/settings/low_a.png"),
            utils.unifiedPath("res/sprites/buttons/settings/med_a.png"),
            utils.unifiedPath("res/sprites/buttons/settings/high_a.png")
        ],
        sfxState
    )
    invertBut = CycleButton(
        (350, 490),
        [
            utils.unifiedPath("res/sprites/buttons/settings/off_n.png"),
            utils.unifiedPath("res/sprites/buttons/settings/on_n.png")
        ],
        [
            utils.unifiedPath("res/sprites/buttons/settings/off_s.png"),
            utils.unifiedPath("res/sprites/buttons/settings/on_s.png")
        ],
        [
            utils.unifiedPath("res/sprites/buttons/settings/off_a.png"),
            utils.unifiedPath("res/sprites/buttons/settings/on_a.png")
        ],
        int(invertXAxis)
    )

    # others
    backdrop: pygame.Surface  = pygame.image.load(utils.unifiedPath("res/sprites/misc/settings.png")) # settings backdrop
    versionText = pygame.Font(regularFont, 20)
    dt: float = 0

    while True:
        # exit input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global running ; running = False
                return
        
        # render
        screen.blit(backdrop)

        render.reset()
        render.setupScene()

        render.drawPolygon(
            shape["vertices"], shape["bases"], shape["quads"], shape["isConvex"],
            utils.uiColors["button_normal"],
            dx = 4, dz = -1, theta = mouseTheta()
        )

        render.finish()
        screen.blit(getGlRender())

        screen.blit( # version text
            versionText.render(utils.versionString, True, utils.uiColors["text"]),
            bottomRightTextPos(versionText, utils.versionString, 30, 20)
        )

        backBut.update(dt)
        musicBut.update(dt)
        sfxBut.update(dt)
        invertBut.update(dt)

        # post-render
        global pageNum, lastPage
        if backBut.clicked:
            pageNum = 0 # go to menu
            lastPage = 3
            return
        
        # update settings
        musicState = musicBut.cycleState
        pygame.mixer.music.set_volume(musicState / 3) # range from 0 to 1

        sfxState = sfxBut.cycleState
        invertXAxis = bool(invertBut.cycleState)

        # final
        pygame.display.flip()
        dt = clock.tick(fps) / 1000

def tutorialPage(bgShape: str):
    "The tutorial page."
    # shape
    shape = polygons.extrude(polygons.get(bgShape))

    # buttons
    backBut = Button(
        (100, 100),
        utils.unifiedPath("res/sprites/buttons/back_n.png"),
        utils.unifiedPath("res/sprites/buttons/back_s.png"),
        utils.unifiedPath("res/sprites/buttons/back_a.png")
    )

    # others
    backdrop: pygame.Surface  = pygame.image.load(utils.unifiedPath("res/sprites/misc/tutorial.png")) # tutorial backdrop
    versionText = pygame.Font(regularFont, 20)
    dt: float = 0

    while True:
        # exit input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global running ; running = False
                return
        
        # render
        screen.blit(backdrop)

        render.reset()
        render.setupScene()

        render.drawPolygon(
            shape["vertices"], shape["bases"], shape["quads"], shape["isConvex"],
            utils.uiColors["button_normal"],
            dx = 4, dz = -1, theta = mouseTheta()
        )

        render.finish()
        screen.blit(getGlRender())

        screen.blit( # version text
            versionText.render(utils.versionString, True, utils.uiColors["text"]),
            bottomRightTextPos(versionText, utils.versionString, 30, 20)
        )

        backBut.update(dt)

        # post-render
        global pageNum, lastPage
        if backBut.clicked:
            pageNum = 0 # go to menu
            lastPage = 4
            return

        # final
        pygame.display.flip()
        dt = clock.tick(fps) / 1000

def creditsPage(bgShape: str):
    "The credits page."
    # shape
    shape = polygons.extrude(polygons.get(bgShape))

    # buttons
    backBut = Button(
        (100, 100),
        utils.unifiedPath("res/sprites/buttons/back_n.png"),
        utils.unifiedPath("res/sprites/buttons/back_s.png"),
        utils.unifiedPath("res/sprites/buttons/back_a.png")
    )

    # others
    backdrop: pygame.Surface  = pygame.image.load(utils.unifiedPath("res/sprites/misc/credits.png")) # credits backdrop
    versionText = pygame.Font(regularFont, 20)
    dt: float = 0

    while True:
        # exit input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global running ; running = False
                return
        
        # render
        screen.blit(backdrop)

        render.reset()
        render.setupScene()

        render.drawPolygon(
            shape["vertices"], shape["bases"], shape["quads"], shape["isConvex"],
            utils.uiColors["button_normal"],
            dx = 4, dz = -1, theta = mouseTheta()
        )

        render.finish()
        screen.blit(getGlRender())

        screen.blit( # version text
            versionText.render(utils.versionString, True, utils.uiColors["text"]),
            bottomRightTextPos(versionText, utils.versionString, 30, 20)
        )

        backBut.update(dt)

        # post-render
        global pageNum, lastPage
        if backBut.clicked:
            pageNum = 0 # go to menu
            lastPage = 5
            return

        # final
        pygame.display.flip()
        dt = clock.tick(fps) / 1000

#-----------------------------------------------------------------------------
# main program control
#-----------------------------------------------------------------------------

pygame.init()

# define pygame things
screen: pygame.Surface = pygame.display.set_mode((width, height))
pygame.display.set_caption("Stack+")
clock = pygame.Clock()

# show loading screen
loadingPage()

# initialize glfw and OpenGL
render.init(width, height, offsetY = 1)

# highscores JSON check
utils.checkHighScoreJson()

# will return to loop after exiting a menu
bgShape: str = None
gameShape: str = None

while running:
    match pageNum:
        case 0: bgShape = menuPage(bgShape)
        case 1: gameShape = levelsPage(bgShape)
        case 2: gamePage(gameShape)
        case 3: settingsPage(bgShape)
        case 4: tutorialPage(bgShape)
        case 5: creditsPage(bgShape)

# end
render.end()
pygame.quit()