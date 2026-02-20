package main

import (
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

type Package struct {
	ID                    uint      `gorm:"primaryKey" json:"id"`
	TrackingID            string    `gorm:"uniqueIndex;not null" json:"tracking_id" binding:"required"` // UUID from locker - collision-resistant across 2000 devices
	LockerID              string    `gorm:"index;not null" json:"locker_id" binding:"required"`          // Identify which locker sent this
	Status                string    `gorm:"not null" json:"status" binding:"required"`
	DropOffTimestamp      time.Time `gorm:"not null" json:"drop_off_timestamp" binding:"required"`      // When customer dropped package (locker's clock)
	SyncAttemptTimestamp  time.Time `gorm:"not null" json:"sync_attempt_timestamp" binding:"required"`  // When locker attempted sync (handles clock drift)
	ServerReceivedAt      time.Time `gorm:"autoCreateTime" json:"server_received_at"`                   // Server's authoritative timestamp (audit trail)
	LastSyncAttempt       int       `gorm:"default:0" json:"last_sync_attempt"`                         // Retry counter from locker
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

		pkg := Package{
			TrackingID:           payload.TrackingID,
			LockerID:             payload.LockerID,
			Status:               payload.Status,
			DropOffTimestamp:     payload.DropOffTimestamp,
			SyncAttemptTimestamp: payload.SyncAttemptTimestamp,
			LastSyncAttempt:      payload.LastSyncAttempt,
		}

		// Idempotent upsert: if locker retries due to timeout/crash, don't create duplicates
		// ON CONFLICT updates only sync metadata, preserves original drop_off data
		result := db.Clauses(clause.OnConflict{
			Columns:   []clause.Column{{Name: "tracking_id"}},
			DoUpdates: clause.AssignmentColumns([]string{"sync_attempt_timestamp", "last_sync_attempt"}),
		}).Create(&pkg)

		if result.Error != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
			return
		}

		// Two-phase commit: send ACK with tracking_id so locker can verify before marking "synced"
		c.JSON(http.StatusCreated, gin.H{
			"tracking_id":        pkg.TrackingID,
			"server_received_at": pkg.ServerReceivedAt,
			"ack":                true,
		})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	if err := router.Run(":" + port); err != nil {
		panic(err)
	}
}
