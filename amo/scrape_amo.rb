require 'rubygems'
require 'hpricot'
require 'net/https'
require 'chronic'

# code that can scrape addons.mozilla.org's extension pages

# copyright 2008, Jesse Andrews, Licensed under GPLv2 or later

class Addon
  require 'hpricot'

  def initialize(id)
    
    @id = id

    @req = Net::HTTP::new('addons.mozilla.org', 443)
    @req.use_ssl = true
    @req.verify_mode = OpenSSL::SSL::VERIFY_NONE

    @res = @req.get("/en-US/firefox/addon/#{id}")
    @hp = Hpricot(@res.body)
  end
  
  def title
    @title = @hp.at("title").inner_text.split(' :: ').first
  end
  
  def authors
        # <h4 class="author">by <a href="/en-US/firefox/user/4195"  class="profileLink">anotherjesse</a>, <a href="/en-US/firefox/user/227354"  class="profileLink">iantriesagain</a>, <a href="/en-US/firefox/user/227355"  class="profileLink">Manish Singh</a></h4>
    @authors = (@hp/"h4.author/a").collect { |author| {:id => author.attributes['href'].split('/').last.to_i, :name => author.inner_text} }
  end
  
  def downloads
    # <p class="stats"><em>4,453</em> downloads</p>
    (@hp.at('.stats/em')).inner_text.gsub(',','').to_i
  end
  
  def ratings
    # <p class="rating">
    # <img src="/img//ratings/5stars.png" width="68" height="12" alt="" title="Rated 5 out of 5 stars"/> 
    # <a href="/en-US/firefox/addon/5756#reviews">13 reviews</a></p>
    {:average => (@hp.at('.rating img')).attributes['title'].split(' ')[1].to_i,
     :quantity => (@hp.at('.rating a')).inner_text.split(' ').first.to_i}
  end

  def categories
    # <ul class="addon-cats">
    #   <li><a href="/en-US/firefox/browse/type:1/cat:22" >Bookmarks</a></li>
    #   <li><a href="/en-US/firefox/browse/type:1/cat:93" >Tabs</a></li>
    # </ul>
    (@hp/".addon-cats/li/a").collect { |cat| cat.inner_text.strip }
  end

  def description
    # <p class="desc">The cure for tabitis<br />
    # <br />
    # If you keep tons of tabs open because you want to continue reading them later, Taboo is for you.  Taboo lets you save a page for later &#40;taking a screenshot, and using the Session Saver code to remember scroll location and form fields&#41;. </p>

    (@hp/"p.desc").inner_html
  end
  
  def images
    # todo
  end
  
  def icon
    # todo
  end
  
  def reviews
    #     <ul class="addon-reviews">
    #         <li id="review-1">
    #           <blockquote>
    #             <p>Wow! I knew within 30 seconds of installing &#39;Taboo&#39; that I needed to add it to my list of must&#45;have add&#45;ons!
    # What a useful little add&#45;on! Thank you!</p>
    #           </blockquote>
    #           <p class="cite">
    # <img src="/img//ratings/5stars.png" width="68" height="12" alt="" title="Rated 5 out of 5 stars"/> 
    #             <cite>
    #             by <a href="/en-US/firefox/user/937135"  class="profileLink">Maddiebeagle</a> on March 29, 2008 (rated 5)            </cite>
    #           </p>
    #         </li>
    (@hp/"ul.addon-reviews/li").collect do |review|
      {:author => {
          :id => review.at('cite/a').attributes['href'].split('/').last,
          :name => review.at('cite/a').inner_text
        },
        :rating => review.at('.cite/img').attributes['title'].split(' ')[1].to_i,
        :created_at => Chronic.parse(review.at('cite').inner_text.split(' on ').last.split(' (').first),
        :body => review.at('blockquote').inner_html
      }
    end
  end

  def to_s
    ["#{title} by #{authors.collect {|a| a[:name]}.join(', ')}",
    "Rating average: #{ratings[:average]} (#{ratings[:quantity]} ratings)",
    "Downloads: #{downloads}",
    "Reviews: #{reviews.length}"].join("\n")
  end

end


# test code:
#
# [5756, 6851, 1843, 3247].each do |id|
#   puts Addon.new(id)
# end
