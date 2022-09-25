# import sys module
import pygame
import sys

class Pausescreen:
  # pygame.init() will initialize all
  # imported module
  def __init__(self):
    pygame.init()
    infoObject = pygame.display.Info()
    self.SCREENWIDTH = infoObject.current_w
    self.SCREENHEIGHT = infoObject.current_h
    self.base_font = pygame.font.Font(None, 32)
    self.color = pygame.Color('chartreuse4')
    self.running = True


  def make_screen(self):
    clock = pygame.time.Clock()
    # it will display on screen
    screen = pygame.display.set_mode([self.SCREENWIDTH, self.SCREENHEIGHT])
    while self.running:
        for event in pygame.event.get():
            # if user types QUIT then the screen will close
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.running = False

        # it will set background color of screen
        screen.fill((255, 255, 255))


        #Then press enter to begin
        enter_text = self.base_font.render("Press Enter to continue", True, (0, 0, 0))
        text_rect = enter_text.get_rect(center=(self.SCREENWIDTH / 2, self.SCREENHEIGHT / 2))
        screen.blit(enter_text, text_rect)

        # display.flip() will update only a portion of the
        # screen to updated, not full area
        pygame.display.flip()

        # clock.tick(60) means that for every second at most
        # 60 frames should be passed.
        clock.tick(60)
    #pygame.quit()
    return
