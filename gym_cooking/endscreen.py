# import sys module
import pygame
import sys

class Endscreen:
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

        thanks_text = self.base_font.render("Thank you for participating", True, (0, 0, 0))
        text_rect = thanks_text.get_rect(center=(self.SCREENWIDTH / 2, self.SCREENHEIGHT / 2 - 100))
        screen.blit(thanks_text, text_rect)

        #Then press enter to begin
        enter_text = self.base_font.render("Press Enter to end the experiment", True, (0, 0, 0))
        text_rect = enter_text.get_rect(center=(self.SCREENWIDTH / 2, self.SCREENHEIGHT / 2))
        screen.blit(enter_text, text_rect)
        pygame.display.flip()
        clock.tick(60)
    #pygame.quit()
    return
