class SiteController < ApplicationController

  def show
    @extensions = Extension.all
  end

end
