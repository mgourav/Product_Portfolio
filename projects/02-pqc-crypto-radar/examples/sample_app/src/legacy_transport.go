package legacytransport

import (
	"crypto/ecdsa"
	"crypto/sha256"
)

func SignLegacy() {
	ecdsa.GenerateKey(nil, nil)
	sha256.New()
}
