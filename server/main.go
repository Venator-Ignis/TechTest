package main

import (
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type Package struct {
	ID         uint      `gorm:"primaryKey" json:"id"`
	TrackingID string    `gorm:"uniqueIndex;not null" json:"tracking_id" binding:"required"`
	Status     string    `gorm:"not null" json:"status" binding:"required"`
	CreatedAt  time.Time `gorm:"not null" json:"created_at" binding:"required"`
}

func main() {
	_ = godotenv.Load()

	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		databaseURL = "postgres://postgres:postgres@localhost:5432/packages?sslmode=disable"
	}

	db, err := gorm.Open(postgres.Open(databaseURL), &gorm.Config{})
	if err != nil {
		panic(err)
	}

	if err := db.AutoMigrate(&Package{}); err != nil {
		panic(err)
	}

	router := gin.Default()
	router.POST("/sync", func(c *gin.Context) {
		var payload Package
		if err := c.ShouldBindJSON(&payload); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		toCreate := Package{
			TrackingID: payload.TrackingID,
			Status:     payload.Status,
			CreatedAt:  payload.CreatedAt,
		}

		if err := db.Create(&toCreate).Error; err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusCreated, toCreate)
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	if err := router.Run(":" + port); err != nil {
		panic(err)
	}
}
