# == Schema Information
#
# Table name: extensions
#
#  id           :integer(4)      not null, primary key
#  mid          :string(255)
#  name         :string(255)
#  icon_url     :string(255)
#  updateRDF    :string(255)
#  description  :text
#  creator      :text
#  homepageURL  :string(255)
#  developers   :text
#  translators  :text
#  contributors :text
#  created_at   :datetime
#  updated_at   :datetime
#

class Extension < ActiveRecord::Base
  has_many :profile_extensions

  serialize :developers
  serialize :translators
  serialize :contributors
end
