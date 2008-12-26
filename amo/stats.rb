require 'csv'
require 'open-uri'

class Addon
  def initialize(id)
    @id = id
  end

  def downloads
    url = "https://addons.mozilla.org/en-US/statistics/csv/#{@id}/downloads"
    data = CSV.parse(open(url).read)
  end
end

taboo = Addon.new(5756)

puts taboo.downloads
