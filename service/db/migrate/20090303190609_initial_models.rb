class InitialModels < ActiveRecord::Migration
  def self.up
    create_table :users do |t|
      t.string :name
      t.timestamps
    end

    create_table :extensions do |t|
      t.string :mid
      t.string :name
      t.string :icon_url
      t.string :updateRDF
      t.text :description
      t.text :creator
      t.string :homepageURL
      t.text :developers
      t.text :translators
      t.text :contributors
      t.timestamps
    end

    create_table :profiles do |t|
      t.integer :user_id
      t.string :name
      t.string :secret
      t.string :os
      t.string :version
      t.string :platform
      t.timestamps
    end

    create_table :profile_extensions do |t|
      t.integer :extension_id
      t.integer :profile_id
      t.string :version
      t.timestamps
    end
  end

  def self.down
    drop_table :users
    drop_table :extensions
    drop_table :profiles
    drop_table :profile_extensions
  end
end
