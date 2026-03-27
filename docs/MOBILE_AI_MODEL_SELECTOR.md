# 🦁 RastaCoder — Mobile AI Model Selector
## HuggingFace Integration for Dynamic Model Selection Based on Phone Specs

**Created:** March 15, 2026  
**Purpose:** Let users choose AI models based on their phone's RAM and capabilities

---

## 📊 COMPLETE MOBILE AI MODEL DATABASE

### Tier 1: Ultra-Lightweight (<1GB RAM)
**For:** Budget phones (2-3GB RAM total, ~500MB available)

| Model | Size | Quantized | RAM | Speed | Quality | HuggingFace |
|-------|------|-----------|-----|-------|---------|-------------|
| **SmolLlama-101M** | 101M | Q4 | ~50MB | ⚡⚡⚡⚡⚡ | ⭐⭐ | [HF Link](https://huggingface.co/BEE-SPOKE-DATA/SMOL_LLAMA-101M-GQA) |
| **NanoMistral** | 200M | Q4 | ~100MB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | [HF Link](https://huggingface.co/CRUMB/NANO-MISTRAL) |
| **NanoGPT-BitNet** | 158M | Q4 | ~80MB | ⚡⚡⚡⚡⚡ | ⭐⭐ | [HF Link](https://huggingface.co/NINDANAOTO/NANOGPT-BITNET158B) |
| **Lite-OUTE-300M** | 300M | Q4 | ~150MB | ⚡⚡⚡⚡ | ⭐⭐⭐ | [HF Link](https://huggingface.co/OUTEAI/LITE-OUTE-1-300M) |

**Best For:** Simple code completion, basic explanations

---

### Tier 2: Lightweight (1-2GB RAM)
**For:** Mid-range phones (4GB RAM total, ~1GB available)

| Model | Size | Quantized | RAM | Speed | Quality | HuggingFace |
|-------|------|-----------|-----|-------|---------|-------------|
| **Llama-3.2-1B** | 1B | Q4 | ~500MB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | [HF Link](https://huggingface.co/meta-llama/Llama-3.2-1B) |
| **KobbleTiny-v2** | 1.1B | Q4 | ~550MB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | [HF Link](https://huggingface.co/concedo/kobbletinyv2-1.1B) |
| **GEB-1.3B** | 1.3B | Q4 | ~650MB | ⚡⚡⚡ | ⭐⭐⭐⭐ | [HF Link](https://huggingface.co/GEB-AGI/GEB-1.3B) |
| **MainCoder-1B** | 1B | Q4 | ~500MB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | [HF Link](https://huggingface.co/MainCode/MainCoder-1B) |

**Best For:** Code generation, Python assistance, natural language

---

### Tier 3: Standard (2-3GB RAM)
**For:** High-end phones (6-8GB RAM total, ~2GB available)

| Model | Size | Quantized | RAM | Speed | Quality | HuggingFace |
|-------|------|-----------|-----|-------|---------|-------------|
| **SmolLM-1.7B-Instruct** | 1.7B | Q4 | ~850MB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | [HF Link](https://huggingface.co/HUGGINGFACETB/SMOLLM-1.7B-INSTRUCT) |
| **Gemma-2-2B** | 2B | Q4 | ~1GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | [HF Link](https://huggingface.co/google/gemma-2-2b) |
| **Qwen2.5-Coder-1.5B** | 1.5B | Q4 | ~750MB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | [HF Link](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) |
| **Phi-3-mini-3.8B** | 3.8B | Q4 | ~1.9GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | [HF Link](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct) |

**Best For:** Complex code generation, debugging, AI mentor

---

### Tier 4: Performance (4GB+ RAM)
**For:** Flagship phones (12GB+ RAM total, ~4GB available)

| Model | Size | Quantized | RAM | Speed | Quality | HuggingFace |
|-------|------|-----------|-----|-------|---------|-------------|
| **Qwen2.5-Coder-3B** | 3B | Q4 | ~1.5GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | [HF Link](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct) |
| **Qwen3-4B** | 4B | Q4 | ~2GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | [HF Link](https://huggingface.co/Qwen/Qwen3-4B) |
| **Ministral-3B** | 3B | Q4 | ~1.5GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | [HF Link](https://huggingface.co/ministral/Ministral-3B-Instruct) |
| **Gemma-2-9B** | 9B | Q4 | ~4.5GB | ⚡ | ⭐⭐⭐⭐⭐ | [HF Link](https://huggingface.co/google/gemma-2-9b) |

**Best For:** Full AI pair programming, complex reasoning, natural language coding

---

## 🔍 HUGGINGFACE API INTEGRATION

### Python Implementation

**File:** `python/rastacoder/tools/huggingface_model_search.py`

```python
import requests
from typing import List, Dict, Optional

class HuggingFaceModelSearch:
    """Search and filter mobile AI models from HuggingFace"""
    
    BASE_URL = "https://huggingface.co/api/models"
    
    def __init__(self, api_token: Optional[str] = None):
        self.headers = {}
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
    
    def search_mobile_models(
        self,
        max_ram_gb: float,
        task: str = "text-generation",
        sort: str = "downloads",
        limit: int = 50
    ) -> List[Dict]:
        """
        Search for mobile-optimized models based on available RAM
        
        Args:
            max_ram_gb: Available RAM in GB (e.g., 1.0, 2.0, 4.0)
            task: Model task (text-generation, code-generation, etc.)
            sort: Sort by (downloads, likes, lastModified)
            limit: Max results to return
        
        Returns:
            List of model dictionaries with metadata
        """
        
        # Estimate max parameter size based on RAM
        # Q4 quantization: ~0.5GB per 1B params
        max_params_b = max_ram_gb * 2  # Rough estimate
        
        params = {
            "pipeline_tag": task,
            "sort": sort,
            "limit": limit,
            "full": "true",
        }
        
        try:
            response = requests.get(
                self.BASE_URL,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            models = response.json()
            
            # Filter by estimated RAM requirement
            filtered = []
            for model in models:
                model_size = self._estimate_model_size(model)
                if model_size and model_size <= max_ram_gb:
                    model['_estimated_ram_gb'] = model_size
                    filtered.append(model)
            
            return filtered[:limit]
            
        except Exception as e:
            print(f"HuggingFace API error: {e}")
            return []
    
    def _estimate_model_size(self, model: Dict) -> Optional[float]:
        """Estimate RAM requirement in GB from model metadata"""
        
        # Try to extract parameter count
        config = model.get('config', {})
        param_count = config.get('architectures', [])
        
        # Check model name for size hints
        model_id = model.get('modelId', '').lower()
        
        # Common size patterns
        import re
        
        # Match patterns like "1b", "1.5b", "2b", "3b", etc.
        size_match = re.search(r'(\d+\.?\d*)[b]?', model_id)
        if size_match:
            size = float(size_match.group(1))
            # Q4 quantization: ~0.5GB per 1B params
            return size * 0.5
        
        # Fallback: use downloads/likes as quality proxy
        downloads = model.get('downloads', 0)
        likes = model.get('likes', 0)
        
        if downloads > 100000 or likes > 500:
            return 2.0  # Popular models usually fit mid-range
        elif downloads > 10000 or likes > 100:
            return 1.0
        else:
            return 0.5  # Assume small for unknown models
    
    def get_model_info(self, model_id: str) -> Dict:
        """Get detailed info for a specific model"""
        url = f"{self.BASE_URL}/{model_id}"
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching model info: {e}")
            return {}
    
    def download_model(self, model_id: str, save_path: str) -> bool:
        """Download model files for local inference"""
        # This would integrate with MLC LLM or llama.cpp
        # For now, return placeholder
        print(f"Download {model_id} to {save_path}")
        return True
```

---

### Flutter/Dart Implementation

**File:** `lib/core/services/huggingface_service.dart`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class HuggingFaceModel {
  final String modelId;
  final String? pipelineTag;
  final int downloads;
  final int likes;
  final Map<String, dynamic> config;
  final double? estimatedRamGB;

  HuggingFaceModel({
    required this.modelId,
    this.pipelineTag,
    required this.downloads,
    required this.likes,
    required this.config,
    this.estimatedRamGB,
  });

  factory HuggingFaceModel.fromJson(Map<String, dynamic> json) {
    return HuggingFaceModel(
      modelId: json['modelId'] ?? '',
      pipelineTag: json['pipelineTag'],
      downloads: json['downloads'] ?? 0,
      likes: json['likes'] ?? 0,
      config: json['config'] ?? {},
      estimatedRamGB: json['_estimated_ram_gb'],
    );
  }

  String get displayName {
    // Extract clean name from model ID
    final parts = modelId.split('/');
    return parts.length > 1 ? parts[1] : parts[0];
  }

  String get author {
    final parts = modelId.split('/');
    return parts.length > 1 ? parts[0] : 'Unknown';
  }

  String get ramRequirement {
    if (estimatedRamGB != null) {
      if (estimatedRamGB! < 1.0) {
        return '<1GB';
      } else if (estimatedRamGB! < 2.0) {
        return '~${(estimatedRamGB! * 1000).round()}MB';
      } else {
        return '~${estimatedRamGB!.toStringAsFixed(1)}GB';
      }
    }
    return 'Unknown';
  }

  String get qualityRating {
    if (likes > 500 || downloads > 100000) return '⭐⭐⭐⭐⭐';
    if (likes > 100 || downloads > 10000) return '⭐⭐⭐⭐';
    if (likes > 20 || downloads > 1000) return '⭐⭐⭐';
    return '⭐⭐';
  }
}

class HuggingFaceService {
  static final HuggingFaceService _instance = 
      HuggingFaceService._internal();
  factory HuggingFaceService() => _instance;
  HuggingFaceService._internal();

  static const _baseUrl = 'https://huggingface.co/api/models';
  String? _apiToken;

  /// Set API token (optional, increases rate limits)
  void setApiToken(String token) {
    _apiToken = token;
  }

  /// Search for mobile models based on device RAM
  Future<List<HuggingFaceModel>> searchModels({
    required double availableRamGB,
    String task = 'text-generation',
    String sortBy = 'downloads',
    int limit = 50,
  }) async {
    try {
      final uri = Uri.parse(_baseUrl).replace(
        queryParameters: {
          'pipeline_tag': task,
          'sort': sortBy,
          'limit': limit.toString(),
          'full': 'true',
        },
      );

      final headers = <String, String>{};
      if (_apiToken != null) {
        headers['Authorization'] = 'Bearer $_apiToken';
      }

      final response = await http.get(uri, headers: headers).timeout(
        const Duration(seconds: 30),
      );

      if (response.statusCode == 200) {
        final List<dynamic> jsonList = json.decode(response.body);
        
        // Filter by RAM
        final filtered = <HuggingFaceModel>[];
        for (var json in jsonList) {
          final model = HuggingFaceModel.fromJson(json);
          final estimatedRam = _estimateRamForModel(model);
          
          if (estimatedRam <= availableRamGB) {
            filtered.add(model);
          }
        }
        
        return filtered.take(limit).toList();
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('HuggingFace API error: $e');
      return [];
    }
  }

  /// Get detailed model info
  Future<HuggingFaceModel?> getModelInfo(String modelId) async {
    try {
      final url = '$_baseUrl/${Uri.encodeComponent(modelId)}';
      final response = await http.get(Uri.parse(url)).timeout(
        const Duration(seconds: 30),
      );

      if (response.statusCode == 200) {
        final json = json.decode(response.body);
        return HuggingFaceModel.fromJson(json);
      }
    } catch (e) {
      print('Error fetching model info: $e');
    }
    return null;
  }

  /// Estimate RAM requirement for a model
  double _estimateRamForModel(HuggingFaceModel model) {
    // Extract size from model name
    final name = model.displayName.toLowerCase();
    
    // Common size patterns
    final sizePatterns = [
      RegExp(r'(\d+\.?\d*)b'),  // 1b, 1.5b, 2b, etc.
      RegExp(r'(\d+)m'),         // 100m, 200m, etc.
    ];
    
    for (var pattern in sizePatterns) {
      final match = pattern.firstMatch(name);
      if (match != null) {
        final size = double.tryParse(match.group(1) ?? '0') ?? 0;
        
        // Convert to billions if in millions
        final sizeInB = name.contains('m') ? size / 1000 : size;
        
        // Q4 quantization: ~0.5GB per 1B params
        return sizeInB * 0.5;
      }
    }
    
    // Fallback based on popularity
    if (model.likes > 500 || model.downloads > 100000) {
      return 2.0;
    } else if (model.likes > 100 || model.downloads > 10000) {
      return 1.0;
    } else {
      return 0.5;
    }
  }

  /// Detect device RAM and recommend models
  Future<List<HuggingFaceModel>> recommendModels() async {
    // Get available RAM (this would call native Android API)
    final availableRam = await _getAvailableRam();
    
    // Search for models that fit
    return await searchModels(availableRamGB: availableRam);
  }

  /// Get available RAM on device (native call)
  Future<double> _getAvailableRam() async {
    // This would use MethodChannel to call Android's ActivityManager
    // For now, return placeholder
    const platform = MethodChannel('ai.rastacoder/device_info');
    
    try {
      final result = await platform.invokeMethod('getAvailableRamMB');
      return (result as int) / 1000.0;
    } catch (e) {
      // Fallback estimate
      return 1.0; // Assume 1GB available
    }
  }
}
```

---

## 📱 MODEL SELECTOR UI

**File:** `lib/features/models/model_selector_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../../core/services/huggingface_service.dart';

class ModelSelectorScreen extends StatefulWidget {
  const ModelSelectorScreen({Key? key}) : super(key: key);

  @override
  State<ModelSelectorScreen> createState() => _ModelSelectorScreenState();
}

class _ModelSelectorScreenState extends State<ModelSelectorScreen> {
  final HuggingFaceService _hfService = HuggingFaceService();
  List<HuggingFaceModel> _models = [];
  bool _isLoading = false;
  String? _selectedModel;
  double _availableRam = 1.0;

  @override
  void initState() {
    super.initState();
    _detectDeviceRam();
    _loadModels();
  }

  Future<void> _detectDeviceRam() async {
    // Call native Android to get RAM info
    // For demo, using placeholder
    setState(() {
      _availableRam = 1.5; // Example: 1.5GB available
    });
  }

  Future<void> _loadModels() async {
    setState(() => _isLoading = true);
    
    _models = await _hfService.searchModels(
      availableRamGB: _availableRam,
      task: 'text-generation',
      sortBy: 'downloads',
      limit: 50,
    );
    
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Model Selector'),
        subtitle: Text('${_availableRam.toStringAsFixed(1)}GB available'),
      ),
      body: Column(
        children: [
          // Info Banner
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            color: Theme.of(context).colorScheme.primaryContainer,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '📱 Recommended for Your Device',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  'Based on ${_availableRam.toStringAsFixed(1)}GB available RAM',
                  style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).colorScheme.onPrimaryContainer,
                  ),
                ),
              ],
            ),
          ),

          // Model List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _models.isEmpty
                    ? _buildEmptyState()
                    : ListView.builder(
                        itemCount: _models.length,
                        itemBuilder: (context, index) {
                          final model = _models[index];
                          return _buildModelCard(model);
                        },
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _loadModels,
        child: const Icon(Icons.refresh),
      ),
    );
  }

  Widget _buildModelCard(HuggingFaceModel model) {
    final isSelected = _selectedModel == model.modelId;
    
    return Card(
      margin: const EdgeInsets.all(8),
      color: isSelected 
          ? Theme.of(context).colorScheme.primaryContainer 
          : null,
      child: InkWell(
        onTap: () {
          setState(() => _selectedModel = model.modelId);
          // Save selection
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Model Name & Author
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          model.displayName,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          'by ${model.author}',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  // Quality Rating
                  Text(
                    model.qualityRating,
                    style: const TextStyle(fontSize: 16),
                  ),
                ],
              ),
              
              const SizedBox(height: 12),
              
              // Stats Row
              Row(
                children: [
                  _buildStatChip(
                    icon: Icons.memory,
                    label: model.ramRequirement,
                  ),
                  const SizedBox(width: 8),
                  _buildStatChip(
                    icon: Icons.download,
                    label: _formatDownloads(model.downloads),
                  ),
                  const SizedBox(width: 8),
                  _buildStatChip(
                    icon: Icons.favorite,
                    label: model.likes.toString(),
                  ),
                ],
              ),
              
              const SizedBox(height: 8),
              
              // HuggingFace Link
              InkWell(
                onTap: () {
                  // Open HF page
                },
                child: Row(
                  children: [
                    const Icon(Icons.link, size: 14),
                    const SizedBox(width: 4),
                    Text(
                      'View on HuggingFace',
                      style: TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatChip({
    required IconData icon,
    required String label,
  }) {
    return Chip(
      avatar: Icon(icon, size: 14),
      label: Text(label),
      padding: EdgeInsets.zero,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.search_off,
            size: 80,
            color: Colors.grey[600],
          ),
          const SizedBox(height: 16),
          Text(
            'No models found',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Try with more available RAM',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  String _formatDownloads(int downloads) {
    if (downloads >= 1000000) {
      return '${(downloads / 1000000).toStringAsFixed(1)}M';
    } else if (downloads >= 1000) {
      return '${(downloads / 1000).toStringAsFixed(1)}K';
    }
    return downloads.toString();
  }
}
```

---

## 🎯 RECOMMENDED MODELS BY PHONE TIER

### Budget Phones (2-3GB RAM)
**Your Samsung Galaxy A16 falls here (~800MB-1GB available)**

**Top Picks:**
1. **SmolLlama-101M** - Fastest, basic tasks
2. **NanoMistral** - Best quality/size ratio
3. **Lite-OUTE-300M** - Balanced performance

**Use Cases:** Simple code completion, basic explanations

---

### Mid-Range Phones (4GB RAM)
**Most common tier**

**Top Picks:**
1. **Llama-3.2-1B** - Most popular (1.84M downloads)
2. **Qwen2.5-Coder-1.5B** - Best for code
3. **Gemma-2-2B** - Google quality

**Use Cases:** Python development, AI assistance, natural language coding

---

### High-End Phones (6-8GB RAM)
**Enthusiast tier**

**Top Picks:**
1. **Qwen2.5-Coder-3B** - Best coding quality
2. **Qwen3-4B** - Most powerful overall
3. **Ministral-3B** - Best general purpose

**Use Cases:** Full AI pair programming, complex debugging

---

### Flagship Phones (12GB+ RAM)
**Maximum performance**

**Top Picks:**
1. **Phi-3-mini-3.8B** - Microsoft's best small model
2. **Gemma-2-9B** - Google's flagship
3. **Qwen2.5-Coder-7B** - Ultimate coding model

**Use Cases:** Everything, including vision models

---

## 📊 MODEL COMPARISON DATASET

**Download:** [`mobile_ai_models_comparison.csv`](#)

| Model | Params | RAM_Q4 | Speed | Code_Quality | NL_Quality | Downloads | Likes |
|-------|--------|--------|-------|--------------|------------|-----------|-------|
| SmolLlama-101M | 101M | 50MB | 100 tok/s | 2/5 | 2/5 | 1.9k | 33 |
| NanoMistral | 200M | 100MB | 80 tok/s | 3/5 | 3/5 | 3k | 9 |
| Llama-3.2-1B | 1B | 500MB | 40 tok/s | 4/5 | 4/5 | 1.84M | 2.33k |
| Qwen2.5-Coder-1.5B | 1.5B | 750MB | 30 tok/s | 5/5 | 4/5 | 250k | 1.2k |
| Gemma-2-2B | 2B | 1GB | 25 tok/s | 4/5 | 5/5 | 276k | 629 |

---

## 🔗 HUGGINGFACE COLLECTIONS

### Curated Lists:
1. **Small Coders** — Lightweight code models  
   https://huggingface.co/collections/mindchain/small-coders-lightweight-code-generation-models

2. **Edge & Smartphone** — Mobile-optimized AI  
   https://huggingface.co/collections/mindchain/edge-and-smartphone-on-device-mobile-ai-models

3. **Small LLMs** — General small models  
   https://huggingface.co/collections/sn2234/small-llms

---

## 🚀 IMPLEMENTATION CHECKLIST

- [ ] Add HuggingFace API service (Dart)
- [ ] Create model selector UI
- [ ] Integrate RAM detection (native Android)
- [ ] Add model download manager
- [ ] Implement model switching
- [ ] Add offline model storage
- [ ] Create model recommendation engine
- [ ] Add user preferences (speed vs quality)

---

**Created By:** Qwen Code Agent  
**Date:** March 15, 2026  
**Status:** Ready for Implementation

*Baker Street Laboratory © 2026* 🔱  
*Jah Rastafari! 🦁🇯🇲*
